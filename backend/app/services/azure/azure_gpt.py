# app/services/azure/azure_gpt.py

from openai import AzureOpenAI, RateLimitError
import threading
from collections import deque
import time
from config import (
    AZURE_GPT_KEY,
    AZURE_GPT_ENDPOINT,
    AZURE_GPT_DEPLOYMENT_BASE,
    AZURE_GPT_API_VERSION,
    TOKENS_PER_MINUTE_BASE,
    MAX_TOTAL_ALLOWED_BASE,
    AZURE_GPT_DEPLOYMENT_ADVANCE,
    TOKENS_PER_MINUTE_ADVANCE,
    MAX_TOTAL_ALLOWED_ADVANCE,
    TOKENIZER,
    MAX_CONCURRENT_REQUESTS
)
from typing import List, Dict, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.gpt_interface import GPTService
from app.models.glossary import Glossary
from app.utils.one_shot import OneShotPairsProvider
from app.utils.parse_response import parse_json_or_key_value_fallback
from app.utils.gpt_messages_builder import MessagesBuilder
from app.utils.prompt_builder import PromptBuilder
from app.utils.llm_roles import LLMRoleProvider
import random
import tiktoken
import logging
import uuid
from collections import deque

logger = logging.getLogger(__name__)

MINIMUM_PASSING_RELEVANCE_SCORE = 7
ATTEMPTS = 3

class TokenTracker:
    def __init__(self, tokens_per_minute: int, max_concurrent_requests: int = 10):
        self.tokens_per_minute = tokens_per_minute
        self.max_concurrent_requests = max_concurrent_requests
        
        # Use separate locks for different operations to reduce contention
        self._history_lock = threading.Lock()
        # Use an RLock here because reserve_tokens() calls _get_used_tokens(),
        # which also tries to acquire this lock. A regular Lock would deadlock
        # when the same thread attempts to re-acquire it.
        self._pending_lock = threading.RLock()
        
        # Store (timestamp, actual_tokens, request_id)
        self._token_history = deque()
        # Track pending requests: {request_id: estimated_tokens}
        self._pending_requests: Dict[str, int] = {}
        
        # Semaphore to limit concurrent requests
        self._request_semaphore = threading.Semaphore(max_concurrent_requests)
        
        # Condition variable for efficient waiting
        self._token_available = threading.Condition()

    def _cleanup_history(self) -> None:
        """Remove entries older than 1 minute. Must be called with history_lock held."""
        cutoff = time.time() - 60
        while self._token_history and self._token_history[0][0] <= cutoff:
            self._token_history.popleft()

    def _get_used_tokens(self) -> Tuple[int, int]:
        """Get currently used tokens. Returns (actual_tokens, pending_tokens)."""
        with self._history_lock:
            self._cleanup_history()
            actual_tokens = sum(tokens for _, tokens, _ in self._token_history)
        
        with self._pending_lock:
            pending_tokens = sum(self._pending_requests.values())
        
        return actual_tokens, pending_tokens

    def _calculate_wait_time(self, needed_tokens: int) -> float:
        """Calculate how long to wait based on token history."""
        with self._history_lock:
            if not self._token_history:
                return 0.0
            
            # Find when we'll have enough tokens available
            current_time = time.time()
            running_total = 0
            
            # Go through history from newest to oldest
            for timestamp, tokens, _ in reversed(self._token_history):
                running_total += tokens
                if running_total >= needed_tokens:
                    # We need to wait until this entry expires
                    wait_time = max(0.0, (timestamp + 60) - current_time + 0.1)  # +0.1s buffer
                    return wait_time
            
            # If we get here, even freeing all history won't be enough
            # Wait for the oldest entry to expire
            oldest_timestamp = self._token_history[0][0]
            return max(1.0, (oldest_timestamp + 60) - current_time + 0.1)

    def reserve_tokens(self, estimated_tokens: int) -> str:
        """Reserve tokens and return a request ID. Blocks if necessary."""
        if estimated_tokens > self.tokens_per_minute:
            raise ValueError(f"Request too large: {estimated_tokens} > {self.tokens_per_minute}")

        # First, acquire semaphore to limit concurrent requests
        if not self._request_semaphore.acquire(timeout=60):
            raise TimeoutError("Too many concurrent requests - request timed out")

        request_id = str(uuid.uuid4())
        
        try:
            with self._token_available:
                while True:
                    with self._pending_lock:
                        actual_tokens, pending_tokens = self._get_used_tokens()
                        total_used = actual_tokens + pending_tokens
                        
                        if total_used + estimated_tokens <= self.tokens_per_minute:
                            self._pending_requests[request_id] = estimated_tokens
                            return request_id
                    
                    # Calculate optimal wait time
                    needed_tokens = total_used + estimated_tokens - self.tokens_per_minute
                    wait_time = self._calculate_wait_time(needed_tokens)
                    
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f}s "
                              f"(used: {total_used}, need: {estimated_tokens})")
                    
                    # Wait for tokens to become available or timeout
                    if not self._token_available.wait(timeout=wait_time + 1.0):
                        # Timeout occurred, try again
                        continue
                        
        except Exception:
            # Release semaphore if reservation fails
            self._request_semaphore.release()
            raise

    def update_actual_tokens(self, request_id: str, actual_tokens: int) -> None:
        """Update with actual token usage after API call completes."""
        try:
            with self._pending_lock:
                if request_id not in self._pending_requests:
                    logger.warning(f"Request ID not found in pending: {request_id[:8]}")
                    return
                
                estimated_tokens = self._pending_requests.pop(request_id)
            
            with self._history_lock:
                self._token_history.append((time.time(), actual_tokens, request_id))
            
            # Notify waiting threads that tokens might be available
            with self._token_available:
                self._token_available.notify_all()
                
        finally:
            # Always release the semaphore
            self._request_semaphore.release()

    def cancel_reservation(self, request_id: str) -> None:
        """Cancel a token reservation (e.g., if request fails)."""
        try:
            with self._pending_lock:
                if request_id in self._pending_requests:
                    estimated = self._pending_requests.pop(request_id)
                else:
                    logger.warning(f"Request ID not found in pending: {request_id[:8]}")
            
            # Notify waiting threads that tokens are available
            with self._token_available:
                self._token_available.notify_all()
                
        finally:
            # Always release the semaphore
            self._request_semaphore.release()

    def get_stats(self) -> Dict[str, int]:
        """Get current token usage statistics."""
        actual_tokens, pending_tokens = self._get_used_tokens()
        available_requests = self._request_semaphore._value
        
        return {
            "actual_tokens_used": actual_tokens,
            "pending_tokens": pending_tokens,
            "total_tokens_used": actual_tokens + pending_tokens,
            "available_tokens": self.tokens_per_minute - (actual_tokens + pending_tokens),
            "available_request_slots": available_requests,
            "active_requests": self.max_concurrent_requests - available_requests
        }


def create_rate_limited_chat_completion(
    deployment_name: str,
    chat_completions_call: callable,
    tokens_per_minute: int,
    max_concurrent_requests: int = 10,
    tokenizer_name: str = "cl100k_base",
    max_response_tokens: int = 4096,
    ) -> callable:
    """
    Create a rate-limited chat completion function.
    
    :param deployment_name: Model deployment name
    :param chat_completions_call: The actual API call function
    :param tokens_per_minute: Rate limit for total tokens per minute
    :param tokenizer_name: Name of the tokenizer to use
    :param max_response_tokens: Maximum tokens allowed in response
    :return: A function that can be called to get chat completions with rate limiting
    """
    token_tracker = TokenTracker(tokens_per_minute, max_concurrent_requests)
    encoding = tiktoken.get_encoding(tokenizer_name)

    def estimate_input_tokens(messages: List[Dict[str, str]]) -> int:
        """Estimate tokens for input messages only."""
        total = 0
        for message in messages:
            # Count content + role + message formatting overhead
            content_tokens = len(encoding.encode(message.get("content", "")))
            role_tokens = len(encoding.encode(message.get("role", "")))
            total += content_tokens + role_tokens + 4  # ~4 tokens overhead per message
        
        # Add some buffer for chat formatting
        return total + 10

    def chat_completion(
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = None,  # Now properly used for response limit
        retries: int = ATTEMPTS,
        **kwargs
    ):
        # Use provided max_tokens or default
        response_limit = max_tokens or max_response_tokens
        
        # Estimate input tokens
        input_tokens = estimate_input_tokens(messages)
        
        # Estimate total tokens (input + expected response)
        # Use a reasonable estimate for response length if not specified
        estimated_response_tokens = min(response_limit, input_tokens // 2)  # Heuristic
        total_estimated = input_tokens + estimated_response_tokens
        
        # Reserve tokens (ONLY ONCE)
        try:
            request_id = token_tracker.reserve_tokens(total_estimated)
        except Exception as e:
            logger.error(f"Failed to reserve tokens: {e}")
            raise
        
        # Retry logic
        try:
            # Make API call with retries
            for attempt in range(retries):
                try:
                    response = chat_completions_call(
                        model=deployment_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens or max_response_tokens,
                        **kwargs
                    )
                    
                    # Get actual token usage
                    if hasattr(response, 'usage') and response.usage:
                        actual_tokens = response.usage.total_tokens
                        logger.debug(f"API response tokens: {actual_tokens} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
                    else:
                        logger.warning("No usage information in API response")
                        actual_tokens = total_estimated  # Fallback
                    
                    # Update with actual usage
                    token_tracker.update_actual_tokens(request_id, actual_tokens)
                    request_id = None  # Prevent double-release
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"API call attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        wait_time = (attempt + 1) * 2
                        time.sleep(wait_time)
                    else:
                        raise
                        
        except Exception as e:
            # Clean up reservation on any error
            if request_id:
                token_tracker.cancel_reservation(request_id)
            raise
    
    return chat_completion

class AzureGPTService(GPTService):
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=AZURE_GPT_KEY,
            azure_endpoint=AZURE_GPT_ENDPOINT,
            api_version=AZURE_GPT_API_VERSION,
        )
        self.base_deployment_name = AZURE_GPT_DEPLOYMENT_BASE
        self.advance_deployment_name = AZURE_GPT_DEPLOYMENT_ADVANCE
        self.chat_completion_base = create_rate_limited_chat_completion(
            deployment_name=self.base_deployment_name,
            chat_completions_call=self.client.chat.completions.create,
            max_concurrent_requests=MAX_CONCURRENT_REQUESTS,
            tokens_per_minute=TOKENS_PER_MINUTE_BASE,
            tokenizer_name=TOKENIZER,
            max_response_tokens=MAX_TOTAL_ALLOWED_BASE
            )
        self.chat_completion_advance = create_rate_limited_chat_completion(
            deployment_name=self.advance_deployment_name,
            chat_completions_call=self.client.chat.completions.create,
            max_concurrent_requests=MAX_CONCURRENT_REQUESTS,
            tokens_per_minute=TOKENS_PER_MINUTE_ADVANCE,
            tokenizer_name=TOKENIZER,
            max_response_tokens=MAX_TOTAL_ALLOWED_ADVANCE
            )

    # Classify input text into one of the provided categories.
    def classify(
        self,
        input_text: str,
        categories: List[str] = None,
        lang: str = "auto",
        max_length: int = 20,
    ) -> str:
        """
        Classify the input text into one of the provided categories.
        
        :param input_text: The text to classify.
        :param categories: List of categories to classify the text into.
        :param lang: Language of the input text, defaults to "auto".
        :param max_length: Maximum length of the category name, defaults to 20.
        :return: The predicted category name.
        :raises ValueError: If no valid response is received from the model or if the category exceeds max_length.
        """
        
        input_text = input_text.strip() if input_text else ""
        if not input_text:
            raise ValueError("Input text cannot be empty or whitespace.")

        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_classification_role())
        builder.add_user(
            PromptBuilder.classify_text_prompt(
                input_text=input_text,
                categories=categories or [],
                lang=lang,
                max_length=max_length,
            )
        )
        messages = builder.build()

        response = self.chat_completion_advance(
            messages=messages, temperature=0.2)

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("No valid response received from the model.")

        category = response.choices[0].message.content.strip()
        # Remove common prefixes in case the model still includes them
        for prefix in ("category:", "Category:", "Label:"):
            if category.lower().startswith(prefix.lower()):
                category = category[len(prefix) :].strip()

        if not category:
            raise ValueError("No category was predicted.")

        if len(category) > max_length:
            category = self._shrink_category(category, lang=lang, max_length=max_length)
            
        return category.title()

    def _shrink_category(self, category: str, lang: str, max_length: int) -> str:
        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_classification_role())
        builder.add_user(
            PromptBuilder.shorten_category_prompt(
                category=category,
                lang=lang,
                max_length=max_length,
            )
        )
        messages = builder.build()
        response = self.chat_completion_base(messages=messages, temperature=0.2)
        shortened = response.choices[0].message.content.strip()
        for prefix in ("category:", "Category:", "Label:"):
            if shortened.lower().startswith(prefix.lower()):
                shortened = shortened[len(prefix):].strip()
        if not shortened:
            raise ValueError("No category was predicted.")
        return shortened

    def create_summary(self, article_texts: List[str], lang: str = "auto") -> str:
        """Generate a summary for the provided article texts."""
        combined_text = ""
        for i, article_text in enumerate(article_texts):
            if article_text and article_text.strip():
                combined_text += f"article {i + 1}:\n {article_text.strip()}\n\n"
            else:
                raise ValueError(f"Article {i + 1} is empty or whitespace.")
        combined_text = combined_text.strip()

        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_summarization_role())
        builder.add_user(PromptBuilder.summary_prompt(article_content=combined_text, lang=lang))
        messages = builder.build()

        response = self.chat_completion_base(messages=messages, temperature=0.3)

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("No summary received from the model.")

        return response.choices[0].message.content.strip()

    def extract_glossary(
        self, article_texts: List[str], lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Extract a glossary of terms from the given article texts.
        The glossary may include acronyms, technical terms, roles, and other key concepts with definitions.

        Args:
            article_texts (List[str]): The texts from which to extract the glossary.
            lang (str): The language of the article. Defaults to "auto".

        Returns:
            dict: A dictionary with terms as keys and definitions as values.
        """
        
        # Step 1 - Connecting the article texts into a single string
        combined_text = ""
        for i, article_text in enumerate(article_texts):
            if article_text and article_text.strip():
                combined_text += f"article {i + 1}:\n {article_text.strip()}\n\n"
            else:
                raise ValueError(
                    f"Article {i + 1} is empty or contains only whitespace."
                )
        combined_text = combined_text.strip()

        # Step 2 - Extracting a list of terms from the articles
        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_glossary_extraction_role())
        builder.add_user(PromptBuilder.term_glossary_extraction_prompt(article_content=combined_text, lang=lang))
        messages = builder.build()
        
        try:
            response = self.chat_completion_base(
                messages=messages, temperature=0.3)
        except Exception as e:
            logger.error(f"Term extraction API call failed: {e}")
            raise
        
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("No glossary received from the model.")

        term_list = response.choices[0].message.content.strip()
        
        # Step 3 - Extracting definitions for the terms
        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_glossary_extraction_role())
        builder.add_user(
            PromptBuilder.definition_glossary_extraction_prompt(
                article_content=combined_text, terms=term_list
            )
        )
        messages = builder.build()
        
        try:
            response = self.chat_completion_base(
                messages=messages, temperature=0.3)
        except Exception as e:
            logger.error(f"Definition extraction API call failed: {e}")
            raise
            
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("No glossary received from the model.")

        term_definition_list = response.choices[0].message.content.strip()

        # Step 4 - Converting the response into JSON format
        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_glossary_extraction_role())
        builder.add_user(PromptBuilder.convert_glossary_to_json_prompt(term_definition_list))
        messages = builder.build()

        try:
            response = self.chat_completion_base(
                messages=messages, temperature=0.3)
        except Exception as e:
            logger.error(f"JSON conversion API call failed: {e}")
            raise
        
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("No glossary received from the model.")

        json_glossary = response.choices[0].message.content.strip()
        
        try:
            glossary = parse_json_or_key_value_fallback(json_glossary)
            return glossary
        except Exception as e:
            logger.error(f"Failed to parse JSON glossary: {e}")
            raise

    def generate_questions(
        self,
        article_texts: List[str],
        lang: str,
        glossary: Glossary = None,
        number_of_questions: int = 10,
        one_shot_examples_to_use: int = 1,
        with_evaluation: bool = True
        ) -> List[Dict[str, Any]]:
        """Generate MCQs for the supplied article texts."""
        if not article_texts or not all(article.strip() for article in article_texts):
            raise ValueError(
                "One or more article texts are empty or contain only whitespace."
            )
        if not lang or lang == "auto":
            raise ValueError("Language must be specified and cannot be 'auto'.")

        questions = []
        article_texts_to_query = AzureGPTService.build_article_blocks(
            article_texts, number_of_questions, 1
        )

        bad_questions: List[Tuple[str, str]] = []

        # parallelize this for each article_text in article_texts_to_query
        with ThreadPoolExecutor() as executor:
            future_to_index = {}
            for i, article_text in enumerate(article_texts_to_query):
                if not article_text or not article_text.strip():
                    raise ValueError(
                        f"Article {i + 1} is empty or contains only whitespace."
                    )

                future = executor.submit(
                    self._generate_question_for_article,
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    bad_questions=bad_questions,
                    lang=lang,
                    with_evaluation=with_evaluation
                )
                future_to_index[future] = i

            for future in as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    question = future.result()
                    questions.append(question)
                except RuntimeError as e:
                    logger.error(f"Error generating question for article {i + 1}: {e}")
                    raise

        return questions[:number_of_questions]
    
    # Generate a question for an article, with retries and improvements.
    def _generate_question_for_article(
        self,
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int,
        bad_questions: List[Tuple[str, str]],
        lang: str,
        with_evaluation: bool = False
        ) -> Dict[str, Any]:
        """Generate and improve a question for a single article."""

        attempts = ATTEMPTS
        chain_of_thought = True
        while attempts > 0:
            try:
                preliminary_question = self.generate_preliminary_question(
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    use_cot=chain_of_thought,
                    bad_questions=bad_questions,
                    lang=lang
                )

                improved_question = self.review_and_improve_question(
                    question=preliminary_question,
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    lang=lang
                )
                
                if with_evaluation:
                    evaluation_result = self.evaluate_question(
                        question=improved_question,
                        article_text=article_text,
                        glossary=glossary,
                        one_shot_examples_to_use=one_shot_examples_to_use * 2,
                        lang=lang
                        )
                    if not evaluation_result:
                        raise ValueError("Question failed evaluation after advanced generation.")

                return improved_question
            except ValueError as e:
                attempts -= 1
                if preliminary_question.get("question", ""):
                    bad_questions.append((preliminary_question.get("question"), f"{e}"))
                if attempts == 0:
                    # Try last time with advanced question generation
                    pass  # Will fall through to advanced method below
            except RuntimeError as e:
                attempts -= 1
                if attempts == 0:
                    raise RuntimeError(f"Question generation failed after {ATTEMPTS} attempts")
                
        # If we reach here, it means all attempts failed, so now we try the advanced method
        preliminary_question = self.generate_preliminary_question_advanced(
            article_text=article_text,
            glossary=glossary,
            one_shot_examples_to_use=one_shot_examples_to_use * 2,
            use_cot=chain_of_thought,
            bad_questions=bad_questions,
            lang=lang
        )

        improved_question = self.review_and_improve_question(
            question=preliminary_question,
            article_text=article_text,
            glossary=glossary,
            one_shot_examples_to_use=one_shot_examples_to_use * 2,
            lang=lang
        )
        
        if with_evaluation:
            evaluation_result = self.evaluate_question(
                question=improved_question,
                article_text=article_text,
                glossary=glossary,
                one_shot_examples_to_use=one_shot_examples_to_use * 2,
                lang=lang
                )
            if not evaluation_result:
                raise ValueError("Question failed evaluation after advanced generation.")
        return improved_question
    
    # Generate a preliminary question based on the article text and glossary.
    def generate_preliminary_question(
        self,
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int = 1,
        use_cot: bool = True,
        bad_questions: List[Tuple[str, str]] = None,
        lang: str = "auto"
    ) -> Dict[str, Any]:
        # Step 1 - Validate inputs ---------------------------------------------------------------------------
        # Check if the article text is empty
        if not article_text or not article_text.strip():
            raise ValueError("Article text is empty or contains only whitespace.")
        
        # Step 2 - Generate the question --------------------------------------------
        # Build the messages for the chat completion
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_creation_role())

        # Add the one-shot examples
        one_shot_examples = OneShotPairsProvider.get_random_mcq_creation_one_shot_pairs(
            n=one_shot_examples_to_use,
            lang=lang
            )
        for user_role, assistant_role in one_shot_examples:
                message_builder.add_user(user_role).add_assistant(assistant_role)
                
        # Building the main prompt
        prompt_builder = PromptBuilder(glossary)
        prompt = prompt_builder.create_question_prompt(
            article_content=article_text.strip(),
            chain_of_thought=use_cot,
            bad_questions=bad_questions,
            lang=lang
            )
        message_builder.add_user(prompt)
        
        messages = message_builder.build()
        
        
        response = self.chat_completion_base(
            messages=messages, temperature=0.0)

        question = response.choices[0].message.content.strip()
        
        # Step 4 - Convert the question to JSON format -------------------------------
        
        message_builder.clear()
        
        message_builder.add_system(LLMRoleProvider.get_mcq_creation_role())
        
        # Add the one-shot examples
        one_shot_examples = OneShotPairsProvider.get_random_mcq_conversion_one_shot_pairs(
            n=one_shot_examples_to_use,
            lang=lang
            )
        for user_role, assistant_role in one_shot_examples:
            message_builder.add_user(user_role).add_assistant(assistant_role)
            
        
        # Building the main prompt
        message_builder.add_user(prompt_builder.convert_question_to_json_prompt(question))
        
        messages = message_builder.build()
        
        response = self.chat_completion_base(
            messages=messages, temperature=0.0)

        question_json = response.choices[0].message.content.strip()
        
        # Step 5 - Parse the JSON response -------------------------------------------------------------------
        
        try:
            question_dict = parse_json_or_key_value_fallback(question_json)
        except ValueError as e:
            raise ValueError(
                f"Failed to parse the question JSON response: {e}. Response content: {question_json}"
            )

        return question_dict
    
    # Advanced version using article summary and main points (A4 and A5 prompts)
    def generate_preliminary_question_advanced(
        self,
        article_text: str,
        glossary: Glossary,
        lang: str,
        one_shot_examples_to_use: int = 1,
        use_cot: bool = True,
        bad_questions: List[Tuple[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate a preliminary question using the main points of the article."""

        if not article_text or not article_text.strip():
            raise ValueError("Article text is empty or contains only whitespace.")
        
        if not lang or lang == "auto":
            raise ValueError("Language must be specified and cannot be 'auto'.")

        # Step A4 - Describe the article and get the key points
        builder = MessagesBuilder()
        builder.add_system(LLMRoleProvider.get_summarization_role())
        prompt = PromptBuilder.describe_article_prompt(
            article_content=article_text.strip(),
            lang=lang
            )
        builder.add_user(prompt)
        messages = builder.build()
        response = self.chat_completion_base(messages=messages, temperature=0.0)
        key_points = response.choices[0].message.content.strip()

        # Step A5 - Create a question from the main points
        builder.clear()
        builder.add_system(LLMRoleProvider.get_mcq_creation_role())
        examples = OneShotPairsProvider.get_random_mcq_creation_one_shot_pairs(n=one_shot_examples_to_use,
                                                                               lang=lang)
        for user_role, assistant_role in examples:
            builder.add_user(user_role).add_assistant(assistant_role)

        prompt_builder = PromptBuilder(glossary)
        prompt=prompt_builder.create_question_from_main_points_prompt(
                article_content=article_text.strip(),
                key_points=key_points,
                chain_of_thought=use_cot,
                lang=lang
            )
        builder.add_user(prompt)
        if bad_questions:
            bad_prompt = "Note: the following are examples of bad questions. Do NOT generate a question similar to them:\n"
            for i, (q, reason) in enumerate(bad_questions, start=1):
                bad_prompt += f"{i}) Question: {q.strip()}\n"
                bad_prompt += f"   Reason: {reason.strip()}\n"
            builder.add_user(bad_prompt)
        messages = builder.build()
        response = self.chat_completion_base(messages=messages, temperature=0.0)
        question = response.choices[0].message.content.strip()

        # Convert the question to JSON
        builder.clear()
        builder.add_system(LLMRoleProvider.get_mcq_creation_role())
        examples = OneShotPairsProvider.get_random_mcq_conversion_one_shot_pairs(n=one_shot_examples_to_use,
                                                                                 lang=lang)
        for user_role, assistant_role in examples:
            builder.add_user(user_role).add_assistant(assistant_role)
        builder.add_user(prompt_builder.convert_question_to_json_prompt(question))
        messages = builder.build()
        response = self.chat_completion_base(messages=messages, temperature=0.0)
        question_json = response.choices[0].message.content.strip()

        try:
            return parse_json_or_key_value_fallback(question_json)
        except ValueError as e:
            raise ValueError(
                f"Failed to parse the question JSON response: {e}. Response content: {question_json}"
            )

    # Review and improve a question based on the article text and glossary.
    def review_and_improve_question(
            self,
            question: Dict[str, Any],
            article_text: str,
            lang: str,
            glossary: Glossary = None,
            one_shot_examples_to_use: int = 1
        ) -> Dict[str, Any]:
            """Review and improve a multiple-choice question."""
            if not article_text or not article_text.strip():
                raise ValueError("Article text is empty or contains only whitespace.")
    
            if not lang or lang == "auto":
                raise ValueError("Language must be specified and cannot be 'auto'.")
            
            critique = self._list_question_errors(
                question=question,
                article_text=article_text,
                glossary=glossary,
                one_shot_examples_to_use=one_shot_examples_to_use,
                lang=lang
            )
            if critique.lower()[:len("no errors found")] != "no errors found":
                improved = self._improve_question_with_critique(
                    question=question,
                    article_text=article_text,
                    critique=critique,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    lang=lang
                )
            else:
                improved = question.copy()

            # Validate and fix language if needed
            try:
                self._validate_language(
                    question=improved, 
                    glossary=glossary, 
                    one_shot_examples_to_use=one_shot_examples_to_use, 
                    lang=lang
                )
            except ValueError as e:
                improved = self._fix_language(
                    question=improved,
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    lang=lang
                )
                
            # Answer the question and fix multiple-correct issues
            improved = self._answer_and_fix(
                question=improved,
                article_text=article_text,
                glossary=glossary,
                one_shot_examples_to_use=one_shot_examples_to_use,
                lang=lang
            )
            
            # Validate and fix grammar if needed
            try:
                self._validate_grammar(
                    question=improved, 
                    glossary=glossary, 
                    one_shot_examples_to_use=one_shot_examples_to_use, 
                    lang=lang
                )
            except ValueError as e:
                improved = self._fix_grammar(
                    question=improved,
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    lang=lang
                )
            # parallelize those next 3 functions, if any fails, kill the living process
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        self._check_external_dependency, improved, article_text, glossary, one_shot_examples_to_use, lang
                    ),
                    executor.submit(
                        self._validate_question_format, improved, article_text, glossary, one_shot_examples_to_use, lang
                    ),
                    executor.submit(
                        self._validate_relevance, improved, article_text, glossary, one_shot_examples_to_use, lang
                    ),
                ]
                for future in as_completed(futures):
                    future.result()
            return improved
   
    # Evaluate a question based on the article text and glossary.
    def evaluate_question(
        self,
        question: Dict[str, Any],
        article_text: str,
        lang: str,
        glossary: Glossary = None,
        one_shot_examples_to_use: int = 1) -> bool:
        """Evaluate a question based on the article text and glossary."""
        if not article_text or not article_text.strip():
            raise ValueError("Article text is empty or contains only whitespace.")
    
        if not lang or lang == "auto":
            raise ValueError("Language must be specified and cannot be 'auto'.")

        try:
            with ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(
                            self._validate_question_format, question, article_text, glossary, one_shot_examples_to_use, lang, self.chat_completion_advance
                        ),
                        executor.submit(
                            self._validate_language, question, glossary, one_shot_examples_to_use, lang, self.chat_completion_advance
                        ),
                        executor.submit(
                            self._validate_grammar, question, glossary, one_shot_examples_to_use, lang, self.chat_completion_advance
                        ),
                        executor.submit(
                            self._validate_relevance, question, article_text, glossary, one_shot_examples_to_use, lang, self.chat_completion_advance
                        ),
                        executor.submit(
                            self._validate_options, question, article_text, glossary, one_shot_examples_to_use, lang, self.chat_completion_advance
                        ), 
                    ]
                    for future in as_completed(futures):
                        future.result()
        except ValueError as e:
            logger.error(f"Question evaluation failed: {e}")
            return False
        
        return True
   
    def _list_question_errors(
            self,
            question: Dict[str, Any],
            article_text: str,
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ) -> str:
            """List issues found in the question."""
            if not chat_completion_call:
                chat_completion_call = self.chat_completion_base
            
            prompt_builder = PromptBuilder(glossary)
            message_builder = MessagesBuilder()
            message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
            examples = OneShotPairsProvider.get_random_mcq_list_errors_one_shot_pairs(
                n=one_shot_examples_to_use,
                lang=lang
            )
            for user_role, assistant_role in examples:
                message_builder.add_user(user_role).add_assistant(assistant_role)
            message_builder.add_user(
                prompt_builder.list_question_errors_prompt(
                    article_content=article_text.strip(),
                    question_text=question
                )
            )
            messages = message_builder.build()
            response = chat_completion_call(messages=messages, temperature=0.0)
            return response.choices[0].message.content.strip()
    
    def _improve_question_with_critique(
            self,
            question: Dict[str, Any],
            article_text: str,
            critique: str,
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ) -> Dict[str, Any]:
            """Improve a question based on critique."""
            if not chat_completion_call:
                chat_completion_call = self.chat_completion_base
            
            message_builder = MessagesBuilder()
            message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
            examples = OneShotPairsProvider.get_random_mcq_improve_one_shot_pairs(
                one_shot_examples_to_use,
                lang=lang
            )
            for user_role, assistant_role in examples:
                message_builder.add_user(user_role).add_assistant(assistant_role)
            prompt_builder = PromptBuilder(glossary)
            message_builder.add_user(
                prompt_builder.improve_question_prompt(
                    article_content=article_text.strip(),
                    question_text=question,
                    critique_text=critique
                )
            )
            messages = message_builder.build()
            response = chat_completion_call(messages=messages, temperature=0.0)
            return parse_json_or_key_value_fallback(response.choices[0].message.content.strip())
    
    def _answer_and_fix(
            self,
            question: Dict[str, Any],
            article_text: str,
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ) -> Dict[str, Any]:
            """Answer the question and fix multiple-correct issues."""
            if not chat_completion_call:
                chat_completion_call = self.chat_completion_base
            
            message_builder = MessagesBuilder()
            message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
            examples = OneShotPairsProvider.get_random_answer_mcq_one_shot_pairs(
                one_shot_examples_to_use,
                lang=lang
            )
            for user_role, assistant_role in examples:
                message_builder.add_user(user_role).add_assistant(assistant_role)
            question_no_answer = question.copy()
            correct = question_no_answer.pop("correct_answer", None)
            prompt_builder = PromptBuilder(glossary)
            message_builder.add_user(
                prompt_builder.answer_question_prompt(
                    article_content=article_text.strip(),
                    question_text=question_no_answer
                )
            )
            messages = message_builder.build()
            response = self.chat_completion_base(messages=messages, temperature=0.0)
            answer = response.choices[0].message.content.strip()[:1]
            if answer.lower() != correct.lower():
                message_builder.clear()
                message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
                ## add one_shot_examples vvv
                
                ## add one_shot_examples ^^^
                message_builder.add_user(
                    prompt_builder.fix_multiple_correct_prompt(
                        article_content=article_text.strip(),
                        question_text=question,
                        lang=lang
                    )
                )
                messages = message_builder.build()
                response = chat_completion_call(messages=messages, temperature=0.0)
                question = parse_json_or_key_value_fallback(response.choices[0].message.content.strip())
            return question
    
    def _check_external_dependency(
            self,
            question: Dict[str, Any],
            article_text: str,
            glossary: Glossary,
            one_shot_examples_to_use:int,
            lang: str,
            chat_completion_call: callable = None
        ) -> None:
            """Ensure the question does not rely on external information."""
            if not chat_completion_call:
                chat_completion_call = self.chat_completion_base
            
            message_builder = MessagesBuilder()
            message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
            examples = OneShotPairsProvider.get_random_external_dependency_one_shot_pairs(
                one_shot_examples_to_use,
                lang=lang
            )
            for user_role, assistant_role in examples:
                message_builder.add_user(user_role).add_assistant(assistant_role)
            prompt_builder = PromptBuilder(glossary)
            message_builder.add_user(
                prompt_builder.external_info_dependency_prompt(
                    article_content=article_text.strip(),
                    question_text=question
                )
            )
            messages = message_builder.build()
            response = chat_completion_call(messages=messages, temperature=0.0)
            if response.choices[0].message.content.strip().lower()[:3] == "yes":
                logger.debug(f"The question depends on external information: #{question}#")
                raise ValueError("The question depends on external information, which is not allowed.")
    
    def _validate_question_format(
            self,
            question: Dict[str, Any],
            article_text: str,
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ) -> None:
        """Validate if the question follows the required format."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        examples = OneShotPairsProvider.get_random_validate_format_one_shot_pairs(
            one_shot_examples_to_use,
            lang=lang
        )
        for user_role, assistant_role in examples:
            message_builder.add_user(user_role).add_assistant(assistant_role)
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.validate_question_format_prompt(
                question_text=question
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        if response.choices[0].message.content.strip().lower()[:2] == "no":
            logger.debug(f"The question does not follow the required format: #{question}#")
            raise ValueError("The question does not follow the required format.")
    
    def _validate_language(
            self,
            question: Dict[str, Any],
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ):
        """Validate if the question is in the correct language."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        examples = OneShotPairsProvider.get_random_validate_language_one_shot_pairs(
            one_shot_examples_to_use,
            lang=lang
        )
        for user_role, assistant_role in examples:
            message_builder.add_user(user_role).add_assistant(assistant_role)
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.validate_language_prompt(
                question_text=question,
                lang=lang
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        if response.choices[0].message.content.strip().lower()[:2] == "no":
            logger.debug(f"The question is not in the correct language: #{question}#")
            raise ValueError("The question is not in the correct language.")

    def _fix_language(
        self,
        question: Dict[str, Any],
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int,
        lang: str,
        chat_completion_call: callable = None
    ) -> Dict[str, Any]:
        """Fix the language of the question."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        examples = OneShotPairsProvider.get_random_fix_language_one_shot_pairs(
            one_shot_examples_to_use,
            lang=lang
        )
        for user_role, assistant_role in examples:
            message_builder.add_user(user_role).add_assistant(assistant_role)
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.fix_language_prompt(
                article_content=article_text.strip(),
                question_text=question,
                lang=lang
            )
        )
        messages = message_builder.build()
        response = self.chat_completion_base(messages=messages, temperature=0.0)
        return parse_json_or_key_value_fallback(response.choices[0].message.content.strip())
    
    def _validate_relevance(
            self,
            question: Dict[str, Any],
            article_text: str,
            glossary: Glossary,
            one_shot_examples_to_use: int,
            lang: str,
            chat_completion_call: callable = None
        ) -> None:
        """Validate if the question is relevant to the article content."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        examples = OneShotPairsProvider.get_random_validate_relevance_one_shot_pairs(
            one_shot_examples_to_use,
            lang=lang
        )
        for user_role, assistant_role in examples:
            message_builder.add_user(user_role).add_assistant(assistant_role)
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.validate_relevance_prompt(
                article_content=article_text.strip(),
                question_text=question
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        score = int(response.choices[0].message.content.strip()[:2])
        if score < MINIMUM_PASSING_RELEVANCE_SCORE:
            logger.debug(f"The question is not relevant enough to the article: #{question}#")
            raise ValueError(
                "The question is not relevant enough to the article core themes and concepts discussed."
            )
    
    def _validate_grammar(
        self,
        question: Dict[str, Any],
        glossary: Glossary,
        one_shot_examples_to_use: int,
        lang: str,
        chat_completion_call: callable = None
    ):
        """Validate if the question has grammatical errors."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        ## add one_shot_examples vvv
        
        ## add one_shot_examples ^^^
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.validate_grammar_prompt(
                question_text=question
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        if response.choices[0].message.content.strip().lower()[:3] == "yes":
            logger.debug(f"The question has grammatical errors: #{question}#")
            raise ValueError("The question has grammatical errors.")

    def _fix_grammar(
        self,
        question: Dict[str, Any],
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int,
        lang: str,
        chat_completion_call: callable = None
    ) -> Dict[str, Any]:
        """Fix grammatical errors in the question."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        ## add one_shot_examples vvv
    
        ## add one_shot_examples ^^^
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.fix_grammar_prompt(
                question_text=question,
                lang=lang
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        return parse_json_or_key_value_fallback(response.choices[0].message.content.strip())
    
    def _validate_options(
        self,
        question: Dict[str, Any],
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int,
        lang: str,
        chat_completion_call: callable = None
    ) -> None:
        """Validate the options of the question by ensuring that the correct answer gets the highest score."""
        if not chat_completion_call:
            chat_completion_call = self.chat_completion_base
        
        correct_answer_key = question.get("correct_answer", "")
        options = question.get("options", {})

        if not options:
            raise ValueError("No options provided in the question.")
        
        # Validate that all options are non-empty
        for i, (key, option_text) in enumerate(options.items()):
            if not option_text or not option_text.strip():
                raise ValueError(f"Option {i + 1} is empty or contains only whitespace.")
        
        # Score options SEQUENTIALLY instead of in parallel to reduce concurrent load
        scores = [0] * len(options)
        for i, (key, option_text) in enumerate(options.items()):
            try:
                scores[i] = self._score_option(
                    question=question,
                    article_text=article_text,
                    glossary=glossary,
                    one_shot_examples_to_use=one_shot_examples_to_use,
                    lang=lang,
                    option_index=i,
                    chat_completion_call=chat_completion_call
                )
            except ValueError as e:
                raise ValueError(f"Failed to score option {i + 1}: {str(e)}")
        
        # Find the score of the correct answer
        correct_answer_score = None
        for i, (key, _) in enumerate(options.items()):
            if key == correct_answer_key:
                correct_answer_score = scores[i]
                break
        
        if correct_answer_score is None:
            raise ValueError("Correct answer key not found in options.")
        
        # Check if correct_answer_score appears more than once (indicating multiple correct answers)
        if scores.count(correct_answer_score) > 1:
            logger.warning(f"Multiple correct answers found for question: {question}. Correct answer score: {correct_answer_score}. Scores: {scores}")
            raise ValueError("Multiple correct answers found, which is not allowed.")
        
        # Check if the correct answer has the highest score
        if correct_answer_score != max(scores):
            logger.warning(f"Correct answer does not have the highest score for question: {question}. Correct answer score: {correct_answer_score}. Scores: {scores}")
            raise ValueError("The correct answer does not have the highest score, which is not allowed.")
        
    def _score_option(
        self,
        question: Dict[str, Any],
        article_text: str,
        glossary: Glossary,
        one_shot_examples_to_use: int,
        lang: str,
        option_index: int,
        chat_completion_call: callable = None
        ) -> int:
        """Score a specific option of the question."""
        options = question.get("options", {})
        question_text = question.get("question", "")
        
        if not question_text or not question_text.strip():
            raise ValueError("Question text is empty or contains only whitespace.")
        
        # Convert integer index to option key and get the text
        option_keys = list(options.keys())
        if option_index >= len(option_keys):
            raise ValueError(f"Option index {option_index} is out of range. Available options: {len(option_keys)}")
        
        option_key = option_keys[option_index]
        answer_option = options[option_key]
        
        message_builder = MessagesBuilder()
        message_builder.add_system(LLMRoleProvider.get_mcq_review_role())
        ## add one_shot_examples vvv
    
        ## add one_shot_examples ^^^
        prompt_builder = PromptBuilder(glossary)
        message_builder.add_user(
            prompt_builder.validate_answer_score_prompt(
                article_content=article_text,
                question_text=question_text,
                answer_option=answer_option,
                glossary=glossary,
            )
        )
        messages = message_builder.build()
        response = chat_completion_call(messages=messages, temperature=0.0)
        score_str = response.choices[0].message.content.strip()
        try:
            score = int(score_str[:2])
            return score
        except ValueError:
            # Fixed: Use option_index instead of option
            logger.error(f"Error casting score to int: {score_str}. Question: {question}. Option: {option_index}")
            raise ValueError(f"Invalid score format: {score_str}. Expected an integer.")
            
        
    # Build article blocks for querying, ensuring each block has a minimum number of texts.
    @staticmethod
    def build_article_blocks(
            article_texts: List[str],
            number_of_questions: int,
            number_of_texts_per_block: int = 2,
        ) -> List[str]:
            article_texts_to_query = []
            num_articles = len(article_texts)
            min_group_size = max(1, number_of_texts_per_block)

            i = 0  # Index to loop through articles
            while len(article_texts_to_query) < number_of_questions:
                # Choose the base article (one that must be in this block)
                base_index = i % num_articles
                other_indices = list(range(num_articles))
                other_indices.remove(base_index)

                # Randomly pick the rest of the group
                num_more = min_group_size - 1
                added_indices = random.sample(other_indices, k=num_more) if num_more > 0 else []

                # Combine base + others
                indices = [base_index] + added_indices
                indices = sorted(indices)
                combined = "\n".join(article_texts[j] for j in indices)
                article_texts_to_query.append(combined)

                i += 1

            return article_texts_to_query





