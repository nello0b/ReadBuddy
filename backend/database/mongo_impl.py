# database/mongo_impl.py

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from database.interface import DatabaseInterface
from config import DATABASE_URL, DATABASE_KEY
from app.models.extraction_result import ExtractionResult
from app.models.image_extraction_result import ImageExtractionResult
from app.models.extraction_result_summary import ExtractionResultSummary
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.answer import Answer
from app.models.glossary import Glossary
from app.models.glossary_entry import GlossaryEntry
from app.models.summary import Summary
import gridfs
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional
from app.utils.text import split_text_into_paragraphs
import os
import uuid
import hashlib


class MongoDB(DatabaseInterface):
    def __init__(self):
        self.client = MongoClient(DATABASE_URL)
        db = self.client["readbuddy"]
        self.users = db["users"]
        self.extraction_result = db["extraction_result"]
        self.audio_chunks = db["audio_chunks"]
        self.media = db["media"]
        self.quiz = db["quiz"]
        self.question = db["question"]
        self.answer = db["answer"]
        self.glossary = db["glossary"]
        self.glossary_entry = db["glossary_entry"]
        self.summary = db["summary"]
        self.deleted_items = db["deleted_items"]
        self.task_status = db["task_status"]
        self.fs_audio = gridfs.GridFS(db, collection="audio_chunks")
        self.fs_media = gridfs.GridFS(db, collection="media")
        self.random_components = db["plan_random_components"]
        
        

    def get_user_by_sub(self, sub: str):
        return self.users.find_one({"sub": sub})

    def create_user(self, user: User):
        return self.users.insert_one(user.to_dict())

    def ping_database(self):
        try:
            self.client.admin.command("ping")
            print("✅ MongoDB is reachable.")
        except PyMongoError as e:
            print("❌ MongoDB is NOT reachable:", e)
            raise RuntimeError("Database unavailable") from e

    # save the image extraction result to the database in a the extraction_result Collection, 
    # also it saves the audio chunks to the audio_chunks Collection and the media to the media Collection
    def save_extraction_result(self, extraction_result: ExtractionResult, media_id: str, user_id: str):
        
        # Save audio chunks using GridFS
        chunk_ids = self.save_audio_chunks(
            audio_zip_urls = extraction_result.audio_zip_urls,
            parent_id = extraction_result.id,
            user_id = user_id,
            parent_type = "extraction_result"
        )
        
        
        result_document = {
            "text_data": extraction_result.text_data,
            "audio_zip_ids": chunk_ids,
            "category": extraction_result.category,
            "media_id": media_id,
            "extraction_id": extraction_result.id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        self.extraction_result.insert_one(result_document)
    
    # Saves audio chunks to GridFS and returns their IDs.
    def save_audio_chunks(self, audio_zip_urls: List[str], parent_id: str, user_id: str, parent_type: str) -> List[str]:
        """
        Saves audio chunks to GridFS and returns their IDs.
        :param audio_zip_urls: List of file paths to audio zip files (can contain None for empty chunks).
        :param parent_id: The ID of the parent object (question, answer, extraction, etc.).
        :param user_id: The user ID.
        :param parent_type: The type of the parent object (e.g., 'question', 'answer', 'extraction_result').
        :return: List of GridFS file IDs (with None for empty chunks).
        """
        chunk_ids = []
        for i, audio_zip_url in enumerate(audio_zip_urls):
            if audio_zip_url is None:
                # Create a placeholder entry for None values (empty paragraphs) but maintain index order
                chunk_id = self.fs_audio.put(
                    b"",  # Empty bytes as placeholder content
                    filename = None,
                    index = i,
                    parent_id = parent_id,
                    parent_type = parent_type,
                    user_id = user_id
                )
                chunk_ids.append(chunk_id)
                continue
                
            with open(audio_zip_url, 'rb') as file_data:
                chunk_id = self.fs_audio.put(
                    file_data,
                    filename = audio_zip_url,
                    index = i,
                    parent_id = parent_id,
                    parent_type = parent_type,
                    user_id = user_id
                )
                chunk_ids.append(chunk_id)
        return chunk_ids
        
    def save_image(self, image_path: str, extraction_id: str, user_id: str):
        # generate a unique name for the image
        name = uuid.uuid4().hex[:12]+".png"
        # Save media files using GridFS
        with open(image_path, 'rb') as media_file:
            media_id  = self.fs_media.put(
                media_file,
                filename=name,
                extraction_id=extraction_id,
                user_id=user_id
            )
        return media_id
    
    def save_image_extraction_result(self, extraction_result: ImageExtractionResult, user_id: str):
        image_id = self.save_image(
            extraction_result.file_path,
            extraction_result.id,
            user_id
        )
        self.save_extraction_result(extraction_result, image_id, user_id)
    
    def get_all_extraction_results_summary(self, user_id: str) -> List[ExtractionResultSummary]:
        results = self.extraction_result.find(
            {"user_id": user_id},
            {"extraction_id": 1, "created_at": 1, "category": 1, "text_data": 1, "_id": 0}
        )
        
        
        summaries = []
        for result in results:
            content = result.get("text_data").get("content", "No Title")
            summary = ExtractionResultSummary(
                extraction_id = result.get("extraction_id"),
                created_at = result.get("created_at"),
                category = result.get("category", "Uncategorized"),
                title = content
            )
            summaries.append(summary)
        return summaries
    
    # Retrieves an extraction result by its ID, and returns the ExtractionResult object and the media file id.
    def get_extraction_result_by_id(self, extraction_id: str, user_id: str) -> Tuple[ExtractionResult, str]:
        result = self.extraction_result.find_one(
            {"extraction_id": extraction_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not result:
            return None, None
        
        # Load the audio chunks by their IDs
        audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)

        return ExtractionResult(
            text_data= result.get("text_data"),
            audio_zip_urls = audio_chunks,
            category=result.get("category"),
            id = result.get("extraction_id"),
            created_at = result.get("created_at")
        ), result.get("media_id")
        
    # Loads audio chunks by their IDs and returns a list of file paths
    def load_audio_chunk_by_id(self, audio_zips_id: List[str], user_id: str) -> List[str]:
        audio_chunks = []
        if not audio_zips_id:
            return audio_chunks
        # Iterate through the audio_zips list and retrieve audio data from GridFS
        for i, chunk in enumerate(audio_zips_id):

            audio_data = self.fs_audio.get(chunk)
            if not audio_data:
                continue
            
            # check if the user_id matches
            if getattr(audio_data, "user_id", None) != user_id:
                raise ValueError("User ID does not match")
            
            if audio_data.filename is not None:
                # split filenameby '/' to get the actual filename
                filename = audio_data.filename.split('/')[-1]
                
                # check that the static directory exists
                os.makedirs("static/audio", exist_ok=True)
                
                # write the audio data to a file
                audio_file_path = f"static/audio/{filename}"
                with open(audio_file_path, 'wb') as audio_file:
                    audio_file.write(audio_data.read())
            else:
                audio_file_path = None
                    
            idx = audio_data.index
            # Expand the list if needed
            while len(audio_chunks) <= idx:
                audio_chunks.append(None)
            audio_chunks[idx] = audio_file_path
            
        return audio_chunks
        
    def load_image_by_id(self, image_id: str, user_id: str):
        try:
            image_data = self.fs_media.get(image_id)
            if not image_data:
                return None
            
            # check if the user_id matches
            if getattr(image_data, "user_id", None) != user_id:
                raise ValueError("User ID does not match")
            
            # split filenameby '/' to get the actual filename
            filename = image_data.filename.split('/')[-1] 
            
            # check that the static directory exists
            os.makedirs("static/image", exist_ok=True)
            
            # Save the image to a temporary file
            file_path = f"static/image/{filename}"
            with open(file_path, 'wb') as temp_file:
                temp_file.write(image_data.read())
                
            return file_path
        except Exception as e:
            print(f"Error loading image by ID {image_id}: {e}")
            return None
        
    def get_image_extraction_result_by_id(self, extraction_id: str, user_id: str) -> ImageExtractionResult:
        extraction_result, media_id = self.get_extraction_result_by_id(extraction_id, user_id)
        if not extraction_result:
            return None
        image_path = self.load_image_by_id(media_id, user_id)
        return ImageExtractionResult(extraction_result = extraction_result, file_path = image_path)
    
    def get_extraction_results_by_ids(self, extraction_ids: List[str], user_id: str) -> List[Tuple[ExtractionResult, str]]:
        if not extraction_ids:
            return []
        
        results = []
        
        # Find extraction results by IDs
        cursor = self.extraction_result.find(
            {"extraction_id": {"$in": extraction_ids}, "user_id": user_id},
            {"_id": 0}
            )
        
        # Iterate through the cursor and build the results list
        for result in cursor:
            audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
            extraction_result = (ExtractionResult(
                text_data = result.get("text_data"),
                audio_zip_urls = audio_chunks,
                category = result.get("category"),
                id = result.get("extraction_id"),
                created_at = result.get("created_at")
            ), result.get("media_id"))
            
            results.append(extraction_result)
            
        return results
    
    def get_image_extraction_results_by_ids(self, extraction_ids: List[str], user_id: str) -> List[ImageExtractionResult]:
        results = []
        extraction_results_plus_media = self.get_extraction_results_by_ids(extraction_ids, user_id)
        for extraction_result, media in extraction_results_plus_media:
            image_path = self.load_image_by_id(media, user_id)
            if image_path:
                image_extraction_result = ImageExtractionResult(
                    extraction_result = extraction_result,
                    file_path = image_path,
                )
                results.append(image_extraction_result)
        return results
        
    def get_extraction_results_by_category(self, category: str, user_id: str) -> List[ImageExtractionResult]:
        cursor = self.extraction_result.find(
            {"category": category, "user_id": user_id},
            {"_id": 0}
        )
        extraction_ids = [result.get("extraction_id") for result in cursor]
        return self.get_image_extraction_results_by_ids(extraction_ids, user_id) if extraction_ids else []
       
    def update_extraction_results_category(self, new_category: str,  extraction_id: str, user_id: str) -> bool:
        result = self.extraction_result.find_one_and_update(
            {"extraction_id": extraction_id, "user_id": user_id},
            {"$set": {"category": new_category}},
            return_document=True
        )
        return result is not None
    
    def get_user_categories(self, user_id: str) -> List[str]:
        summaries = self.get_all_extraction_results_summary(user_id)
        return list({s.category for s in summaries if s.category})
    
    # Saves a quiz to the database.
    def save_quiz(self, quiz: Quiz):
        self.quiz.insert_one(quiz.to_dict())
    
    # Retrieves a quiz by its ID and user ID, returning a Quiz object.
    def get_quiz_by_id(self, quiz_id: str, user_id: str) -> Quiz:
        result = self.quiz.find_one(
            {"id": quiz_id, "user_id": user_id},
            {"_id": 0}
        )
        
        # If no quiz is found, return None
        if not result:
            return None
        
        # Create a Quiz object from the dictionary
        return Quiz(
            user_id = result.get("user_id"),
            title = result.get("title"),
            category = result.get("category"),
            question_ids = result.get("question_ids", []),
            id = result.get("id"),
            created_at = result.get("created_at")
        )
    
    # Retrieves all quizzes for a given user ID, returning a list of Quiz objects.
    def get_quizzes_by_user_id(self, user_id: str) -> List[Quiz]:
        results = self.quiz.find(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        # Convert the cursor to a list of Quiz objects
        results = list(results)
        return [Quiz(
            user_id = q.get("user_id"),
            title = q.get("title"),
            category = q.get("category"),
            question_ids = q.get("question_ids", []),
            id = q.get("id"),
            created_at = q.get("created_at")
        ) for q in results]
    
    # Retrieves a question by its ID and user ID, loading the associated audio chunks.
    def get_question_by_id(self, question_id: str, user_id: str) -> Question:
        result = self.question.find_one(
            {"id": question_id, "user_id": user_id},
            {"_id": 0}
        )
        
        # If no question is found, return None
        if not result:
            return None
        
        # Load the audio chunks by their IDs
        audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
        
        # Create a Question object from the dictionary
        return Question(
            id = result.get("id"),
            user_id = result.get("user_id"),
            content = result.get("content"),
            answers = self.get_answers_by_ids(result.get("answer_ids", []), user_id),
            correct_answer_id = result.get("correct_answer_id"),
            audio_zip_urls = audio_chunks
        )
        
    # Retrieves questions by their IDs and user ID, returning a list of Question objects.
    def get_questions_by_ids(self, question_ids: List[str], user_id: str) -> List[Question]:
        if not question_ids:
            return []
        
        # Find questions by IDs and user ID
        cursor = self.question.find(
            {"id": {"$in": question_ids}, "user_id": user_id},
            {"_id": 0}
        )
        
        # Iterate through the cursor and build the questions list
        questions = []
        for result in cursor:
            audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
            question = Question(
                id = result.get("id"),
                user_id = result.get("user_id"),
                content = result.get("content"),
                answers = self.get_answers_by_ids(result.get("answer_ids", []), user_id),
                correct_answer_id = result.get("correct_answer_id"),
                audio_zip_urls = audio_chunks
            )
            questions.append(question)
            
        return questions
    
    # Saves a list of questions to the database, including their answers and audio chunks.
    def save_questions(self, questions: List[Question], user_id: str):
        for question in questions:
            self.save_question(question, user_id)
    
    # Saves a question to the database, including its answers and audio chunks.
    def save_question(self, question: Question, user_id: str):
        # Save the answers
        for answer in question.answers:
            self.save_answer(answer, user_id)
        
        chunk_ids = []
        if question.audio_zip_urls != None:
            # Save the audio_zip_urls
            chunk_ids = self.save_audio_chunks(
                audio_zip_urls = question.audio_zip_urls,
                parent_id = question.id,
                user_id = user_id,
                parent_type = "question"
            )
        
        question_document = {
            "id": question.id,
            "user_id": user_id,
            "content": question.content,
            "answer_ids": [answer.id for answer in question.answers],
            "correct_answer_id": question.correct_answer_id,
            "audio_zip_ids": chunk_ids
        }
        
        # Insert the question document into the database
        self.question.insert_one(question_document)
    
    # Updates a question in the database, including its answers and audio chunks.
    def update_question(self, question: Question, user_id: str):
        # Save the answers (update or insert)
        for answer in question.answers:
            self.update_answer(answer, user_id)

        chunk_ids = []
        if question.audio_zip_urls is not None:
            chunk_ids = self.save_audio_chunks(
                audio_zip_urls=question.audio_zip_urls,
                parent_id=question.id,
                user_id=user_id,
                parent_type="question"
            )

        update_fields = {
            "content": question.content,
            "answer_ids": [answer.id for answer in question.answers],
            "correct_answer_id": question.correct_answer_id,
            "audio_zip_ids": chunk_ids
        }

        result = self.question.update_one(
            {"id": question.id, "user_id": user_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    # Updates an answer in the database, including its audio chunks.
    def update_answer(self, answer: Answer, user_id: str):
        chunk_ids = []
        if answer.audio_zip_urls is not None:
            chunk_ids = self.save_audio_chunks(
            audio_zip_urls=answer.audio_zip_urls,
            parent_id=answer.id,
            user_id=user_id,
            parent_type="answer"
            )

        update_fields = {
            "content": answer.content,
            "audio_zip_ids": chunk_ids
        }

        result = self.answer.update_one(
            {"id": answer.id, "user_id": user_id},
            {"$set": update_fields}
        )
        return result.modified_count > 0
      
    # Saves an answer to the database, including its audio chunks.
    def save_answer(self, answer: Answer, user_id: str):
        # Save the audio_zip_urls
        chunk_ids = self.save_audio_chunks(
            audio_zip_urls = answer.audio_zip_urls,
            parent_id = answer.id,
            user_id = user_id,
            parent_type = "answer"
        )
        
        answer_document = {
            "id": answer.id,
            "user_id": user_id,
            "content": answer.content,
            "audio_zip_ids": chunk_ids
        }
        
        # Insert the answer document into the database
        self.answer.insert_one(answer_document)
        
    # Retrieves an answer by its ID and user ID, loading the associated audio chunks.
    def get_answer_by_id(self, answer_id: str, user_id: str) -> Answer:
        # Retrieve the answer document by ID and user ID
        result = self.answer.find_one(
            {"id": answer_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not result:
            return None
        
        # Load the audio chunks by their IDs
        audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
        
        # Create an Answer object from the dictionary
        return Answer(
            id = result.get("id"),
            user_id = result.get("user_id"),
            content = result.get("content"),
            audio_zip_urls = audio_chunks
        )

    # Retrieves answers by their IDs and user ID, returning a list of Answer objects.
    def get_answers_by_ids(self, answer_ids: List[str], user_id: str) -> List[Answer]:
        if not answer_ids:
            return []
        
        # Find answers by IDs and user ID
        cursor = self.answer.find(
            {"id": {"$in": answer_ids}, "user_id": user_id},
            {"_id": 0}
        )
        
        # Iterate through the cursor and build the answers list
        answers = []
        for result in cursor:
            audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
            answer = Answer(
                id = result.get("id"),
                user_id = result.get("user_id"),
                content = result.get("content"),
                audio_zip_urls = audio_chunks
            )
            answers.append(answer)
            
        return answers
    
    # Retrieves quizzes by category and user ID, returning a list of Quiz objects.
    def get_quizzes_by_category(self, category: str, user_id: str) -> List[Quiz]:
        cursor = self.quiz.find(
            {"category": category, "user_id": user_id},
            {"_id": 0}
        )
        
        # Convert the cursor to a list of Quiz objects
        results = list(cursor)
        return [Quiz(
            user_id = q.get("user_id"),
            title = q.get("title"),
            category = q.get("category"),
            question_ids = q.get("question_ids", []),
            id = q.get("id"),
            created_at = q.get("created_at")
        ) for q in results]
    
    # Saves a glossary to the database.
    def save_glossary(self, glossary: Glossary, user_id: str):
        # save the glossary entries
        for entry in glossary.entries:
            self.save_glossary_entry(entry, user_id)
            
        # Create a glossary document
        glossary_document = {
            "id": glossary.id,
            "user_id": user_id,
            "category": glossary.category,
            "entry_ids": [entry.id for entry in glossary.entries],
            "last_updated": glossary.last_updated
        }
        
        # Insert the glossary document into the database
        self.glossary.insert_one(glossary_document)
    
    def save_glossary_entry(self, entry: GlossaryEntry, user_id: str):
        """
        Saves a glossary entry to the database.
        :param entry: The GlossaryEntry object to save.
        :param user_id: The user ID associated with the entry.
        """
        # Save the audio chunks for the term and definition
        term_chunk_ids = self.save_audio_chunks(
            audio_zip_urls = entry.term_audio_zip_urls,
            parent_id = entry.id,
            user_id = user_id,
            parent_type = "glossary_entry_term"
        )
        
        definition_chunk_ids = self.save_audio_chunks(
            audio_zip_urls = entry.definition_audio_zip_urls,
            parent_id = entry.id,
            user_id = user_id,
            parent_type = "glossary_entry_definition"
        )
        
        entry_document = {
            "id": entry.id,
            "term": entry.term,
            "definition": entry.definition,
            "term_audio_zip_ids": term_chunk_ids if term_chunk_ids else [],
            "definition_audio_zip_ids": definition_chunk_ids if definition_chunk_ids else [],
            "user_id": user_id
        }
        
        # Insert the glossary entry document into the database
        self.glossary_entry.insert_one(entry_document)

    def update_glossary_entry(self, entry: GlossaryEntry, user_id: str):
        """Update an existing glossary entry including its audio chunks."""
        term_chunk_ids = self.save_audio_chunks(
            audio_zip_urls=entry.term_audio_zip_urls,
            parent_id=entry.id,
            user_id=user_id,
            parent_type="glossary_entry_term",
        )

        definition_chunk_ids = self.save_audio_chunks(
            audio_zip_urls=entry.definition_audio_zip_urls,
            parent_id=entry.id,
            user_id=user_id,
            parent_type="glossary_entry_definition",
        )

        update_fields = {
            "term": entry.term,
            "definition": entry.definition,
            "term_audio_zip_ids": term_chunk_ids,
            "definition_audio_zip_ids": definition_chunk_ids,
        }

        self.glossary_entry.update_one(
            {"id": entry.id, "user_id": user_id},
            {"$set": update_fields},
        )
    
    # Retrieves a glossary by its ID and user ID, returning a Glossary object.
    def get_glossary_by_id(self, glossary_id: str, user_id: str) -> Glossary:
        result = self.glossary.find_one(
            {"id": glossary_id, "user_id": user_id},
            {"_id": 0}
        )
        
        # If no glossary is found, return None
        if not result:
            return None
        
        # Retrieve the entries for the glossary
        entries = self.get_glossary_entries_by_ids(result.get("entry_ids", []), user_id)
        
        # Create a Glossary object from the dictionary
        return Glossary(
            id = result.get("id"),
            category = result.get("category"),
            user_id = result.get("user_id"),
            entries = entries,
            last_updated = result.get("last_updated")
        )
    
    # Retrieves glossary entries by their IDs and user ID, returning a list of GlossaryEntry objects.
    def get_glossary_entries_by_ids(self, entry_ids: List[str], user_id: str) -> List[GlossaryEntry]:
        if not entry_ids:
            return []
        
        # Find glossary entries by IDs and user ID
        cursor = self.glossary_entry.find(
            {"id": {"$in": entry_ids}, "user_id": user_id},
            {"_id": 0}
        )
        
        # Iterate through the cursor and build the entries list
        entries = []
        for result in cursor:
            term_audio_chunks = self.load_audio_chunk_by_id(result.get("term_audio_zip_ids", []), user_id)
            definition_audio_chunks = self.load_audio_chunk_by_id(result.get("definition_audio_zip_ids", []), user_id)
            
            entry = GlossaryEntry(
                id = result.get("id"),
                term = result.get("term"),
                definition = result.get("definition"),
                term_audio_zip_urls = term_audio_chunks,
                definition_audio_zip_urls = definition_audio_chunks,
                user_id = result.get("user_id")
            )
            entries.append(entry)
            
        return entries

    def get_all_glossaries(self, user_id: str) -> List[Glossary]:
        cursor = self.glossary.find(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        # Convert the cursor to a list of Glossary objects
        results = list(cursor)
        glossaries = []
        for g in results:
            entries = self.get_glossary_entries_by_ids(g.get("entry_ids", []), user_id)
            glossaries.append(
                Glossary(
                    id=g.get("id"),
                    category=g.get("category"),
                    user_id=g.get("user_id"),
                    entries=entries,
                    last_updated=g.get("last_updated")
                )
            )
        return glossaries

    def save_summary(self, summary: Summary, user_id: str):
        chunk_ids = []
        if summary.audio_zip_urls:
            chunk_ids = self.save_audio_chunks(
                audio_zip_urls=summary.audio_zip_urls,
                parent_id=summary.id,
                user_id=user_id,
                parent_type="summary",
            )
        doc = {
            "id": summary.id,
            "user_id": user_id,
            "source_ids": summary.source_ids,
            "content": summary.content,
            "audio_zip_ids": chunk_ids,
            "created_at": summary.created_at,
        }
        self.summary.insert_one(doc)

    def get_summary_by_id(self, summary_id: str, user_id: str) -> Summary:
        result = self.summary.find_one({"id": summary_id, "user_id": user_id}, {"_id": 0})
        if not result:
            return None
        audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
        content = result.get("content", [])
        if isinstance(content, str):
            content = split_text_into_paragraphs(content)
        return Summary(
            source_ids=result.get("source_ids", []),
            content=content,
            audio_zip_urls=audio_chunks,
            id=result.get("id"),
            created_at=result.get("created_at"),
        )

    def delete_summary(self, summary_id: str, user_id: str) -> bool:
        doc = self.summary.find_one({"id": summary_id, "user_id": user_id})
        if not doc:
            return False
        self.log_deleted_item("summary", doc, user_id)
        for cid in doc.get("audio_zip_ids", []):
            try:
                self.fs_audio.delete(cid)
            except Exception:
                pass
        self.summary.delete_one({"id": summary_id, "user_id": user_id})
        return True

    def update_summary(self, summary: Summary, user_id: str):
        chunk_ids = []
        if summary.audio_zip_urls:
            chunk_ids = self.save_audio_chunks(
                audio_zip_urls=summary.audio_zip_urls,
                parent_id=summary.id,
                user_id=user_id,
                parent_type="summary",
            )
        update = {
            "source_ids": summary.source_ids,
            "content": summary.content,
            "audio_zip_ids": chunk_ids,
        }
        self.summary.update_one({"id": summary.id, "user_id": user_id}, {"$set": update})

    def get_summaries_by_user_id(self, user_id: str) -> List[Summary]:
        cursor = self.summary.find({"user_id": user_id}, {"_id": 0})
        summaries = []
        for result in cursor:
            audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
            content = result.get("content", [])
            if isinstance(content, str):
                content = split_text_into_paragraphs(content)
            summaries.append(Summary(
                source_ids=result.get("source_ids", []),
                content=content,
                audio_zip_urls=audio_chunks,
                id=result.get("id"),
                created_at=result.get("created_at"),
            ))
        return summaries

    def get_summaries_by_source_id(self, source_id: str, user_id: str) -> List[Summary]:
        cursor = self.summary.find({"source_ids": {"$in": [source_id]}, "user_id": user_id}, {"_id": 0})
        summaries = []
        for result in cursor:
            audio_chunks = self.load_audio_chunk_by_id(result.get("audio_zip_ids", []), user_id)
            content = result.get("content", [])
            if isinstance(content, str):
                content = split_text_into_paragraphs(content)
            summaries.append(Summary(
                source_ids=result.get("source_ids", []),
                content=content,
                audio_zip_urls=audio_chunks,
                id=result.get("id"),
                created_at=result.get("created_at"),
            ))
        return summaries

    def log_deleted_item(self, item_type: str, data: dict, user_id: str):
        self.deleted_items.insert_one({
            "item_type": item_type,
            "data": data,
            "user_id": user_id,
            "deleted_at": datetime.now(timezone.utc).isoformat()
        })

    def delete_image_extraction_result(self, extraction_id: str, user_id: str) -> bool:
        doc = self.extraction_result.find_one({"extraction_id": extraction_id, "user_id": user_id})
        if not doc:
            return False
        self.log_deleted_item("image_extraction_result", doc, user_id)
        for chunk_id in doc.get("audio_zip_ids", []):
            try:
                self.fs_audio.delete(chunk_id)
            except Exception:
                pass
        media_id = doc.get("media_id")
        if media_id:
            try:
                self.fs_media.delete(media_id)
            except Exception:
                pass
        self.extraction_result.delete_one({"extraction_id": extraction_id, "user_id": user_id})
        return True

    def delete_quiz(self, quiz_id: str, user_id: str) -> bool:
        quiz_doc = self.quiz.find_one({"id": quiz_id, "user_id": user_id})
        if not quiz_doc:
            return False
        self.log_deleted_item("quiz", quiz_doc, user_id)
        question_ids = quiz_doc.get("question_ids", [])
        if question_ids:
            for qid in question_ids:
                self.delete_question(qid, user_id)
        self.quiz.delete_one({"id": quiz_id, "user_id": user_id})
        return True

    def delete_glossary(self, glossary_id: str, user_id: str) -> bool:
        glos_doc = self.glossary.find_one({"id": glossary_id, "user_id": user_id})
        if not glos_doc:
            return False
        self.log_deleted_item("glossary", glos_doc, user_id)
        entry_ids = glos_doc.get("entry_ids", [])
        for eid in entry_ids:
            self.delete_glossary_entry(eid, user_id)
        self.glossary.delete_one({"id": glossary_id, "user_id": user_id})
        return True

    def delete_question(self, question_id: str, user_id: str) -> bool:
        qdoc = self.question.find_one({"id": question_id, "user_id": user_id})
        if not qdoc:
            return False
        self.log_deleted_item("question", qdoc, user_id)
        self.quiz.update_many({"question_ids": question_id, "user_id": user_id}, {"$pull": {"question_ids": question_id}})
        for chunk_id in qdoc.get("audio_zip_ids", []):
            try:
                self.fs_audio.delete(chunk_id)
            except Exception:
                pass
        answer_ids = qdoc.get("answer_ids", [])
        for aid in answer_ids:
            self.delete_answer(aid, user_id)
        self.question.delete_one({"id": question_id, "user_id": user_id})
        return True

    def delete_answer(self, answer_id: str, user_id: str) -> bool:
        adoc = self.answer.find_one({"id": answer_id, "user_id": user_id})
        if not adoc:
            return False
        self.log_deleted_item("answer", adoc, user_id)
        self.question.update_many({"answer_ids": answer_id, "user_id": user_id}, {"$pull": {"answer_ids": answer_id}})
        self.question.update_many({"correct_answer_id": answer_id, "user_id": user_id}, {"$set": {"correct_answer_id": None}})
        for chunk_id in adoc.get("audio_zip_ids", []):
            try:
                self.fs_audio.delete(chunk_id)
            except Exception:
                pass
        self.answer.delete_one({"id": answer_id, "user_id": user_id})
        return True

    def delete_glossary_entry(self, entry_id: str, user_id: str) -> bool:
        edoc = self.glossary_entry.find_one({"id": entry_id, "user_id": user_id})
        if not edoc:
            return False
        self.log_deleted_item("glossary_entry", edoc, user_id)
        for cid in edoc.get("term_audio_zip_ids", []):
            try:
                self.fs_audio.delete(cid)
            except Exception:
                pass
        for cid in edoc.get("definition_audio_zip_ids", []):
            try:
                self.fs_audio.delete(cid)
            except Exception:
                pass
        self.glossary_entry.delete_one({"id": entry_id, "user_id": user_id})
        return True


    def save_task_state(self, task_id: str, state: str, meta: dict):
        """
        Saves the task state to the database.
        
        :param task_id: The ID of the task.
        :param status: The status of the task (e.g., "STARTED", "PROGRESS", "SUCCESS", "FAILURE").
        :param meta: Additional metadata about the task.
        """
        
        existing = self.task_status.find_one({"task_id": task_id})
        task_status = {
            "task_id": task_id,
            "state": state,
            "meta": meta,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if existing:
            self.task_status.update_one({"task_id": task_id}, {"$set": task_status})
        else:
            self.task_status.insert_one(task_status)
            
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        Retrieves the task status by task ID.
        
        :param task_id: The ID of the task.
        :return: A dictionary containing the task status and metadata, or None if not found.
        """
        result = self.task_status.find_one({"task_id": task_id}, {"_id": 0})
        return result if result else None
    
    
    def plan_database_empty(self, secret: str, keep_collections: List[str] = []) -> dict:
        """
        Plan what collections will be dropped without actually dropping them.
        
        :param secret: The secret key to authorize the operation.
        :param keep_collections: Collections to keep
        :return: Dictionary with plan details
        """
        if isinstance(keep_collections, str):
            keep_collections = [keep_collections]
        
        if DATABASE_KEY != secret:
            raise ValueError("Invalid secret key")
        
        # Default collections to always keep
        ALWAYS_KEEP = ["users", "plan_random_components"]
        
        # Get actual collections from your database
        all_collections = self.client["readbuddy"].list_collection_names()
        
        # Validate that all keep_collections actually exist
        invalid_keep = [col for col in keep_collections if col not in all_collections]
        if invalid_keep:
            raise ValueError(f"Invalid collection names in keep_collections: {invalid_keep}. "
                           f"Available collections: {all_collections}")
        
        for col in ALWAYS_KEEP:
            if col not in keep_collections:
                keep_collections.append(col)
        
        collections_to_drop = [col for col in all_collections if col not in keep_collections]
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        plan_without_token = {
            "total_collections": len(all_collections),
            "collections_to_drop": collections_to_drop,
            "collections_to_keep": keep_collections,
            "plan_created_at": timestamp
            }
        
        # Generate a secure, unpredictable token (not based on secret)
        random_component = os.urandom(16).hex()  # 32 character random string
        # save the ramdom component to the database for later verification
        self.random_components.insert_one({
            "random_component": random_component,
            "created_at": timestamp
        })
        
        confirmation_token = hashlib.sha256(f"{timestamp}:{random_component}:{plan_without_token}".encode()).hexdigest()[:16]
        
        plan_without_token["confirmation_token"] = confirmation_token
        
        return plan_without_token
    
    def _verify_plan(self, plan: dict, timeout = 300) -> bool:
        """
        Verify the confirmation token in the plan.
        
        :param plan: The plan returned from plan_database_empty
        :param timeout: The maximum time in seconds for the plan to be valid (default is 5 minutes)
        :return: True if the token is valid, False otherwise
        """
        # step 0: clean up expired tokens
        self._cleanup_expired_tokens(timeout)
        
        if not isinstance(plan, dict):
            return False
        
        # step 1: check if the plan has expired
        try:
            plan_created = plan.get("plan_created_at")
            if not plan_created:
                return False
            plan_time = datetime.fromisoformat(plan_created.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if (now - plan_time.replace(tzinfo=timezone.utc)).total_seconds() > timeout:
                return False  # Plan has expired
        except (ValueError, AttributeError):
            return False  # Invalid timestamp format   
        
        # step 2: check the confirmation token
        try:
            confirmation_token = plan.get("confirmation_token")
            if not confirmation_token:
                return False  # Invalid or missing confirmation token
            
            # Remove the confirmation token from the plan for verification
            plan_without_token = plan.copy()
            plan_without_token.pop("confirmation_token", None)
            
            # Retrieve the random component from the database
            random_component_doc = self.random_components.find_one({"created_at": plan.get("plan_created_at")})
            if not random_component_doc:
                return False
            
            # Generate the expected token
            expected_token = hashlib.sha256(f"{plan['plan_created_at']}:{random_component_doc['random_component']}:{plan_without_token}".encode()).hexdigest()[:16]
            
            # Compare the provided token with the expected token
            return confirmation_token == expected_token
        except Exception:
            return False
        

    def execute_database_empty(self, plan: dict):
        """
        Execute the database empty plan with confirmation token.
        
        :param plan: The plan returned from plan_database_empty
        """
        
        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")
        
        if plan.get('collections_to_drop', None) is None or not isinstance(plan.get('collections_to_drop'), list):
            raise ValueError("Plan must contain a list of 'collections_to_drop'")
        
        # Verify the confirmation token exists in the plan
        confirmation_token = plan.get("confirmation_token")
        if not confirmation_token:
            raise ValueError("Invalid or missing confirmation token")
        
        if not self._verify_plan(plan):
            raise ValueError("Invalid confirmation token or plan has expired")
        
        collections_to_drop = plan.get("collections_to_drop", [])
        
        print(f"Executing database cleanup plan...")
        print(f"Will drop {len(collections_to_drop)} collections: {collections_to_drop}")
        print(f"Will keep {len(plan.get('collections_to_keep', []))} collections: {plan.get('collections_to_keep', [])}")
        
        # Safety check
        if len(collections_to_drop) > 5:
            print(f"WARNING: About to drop {len(collections_to_drop)} collections!")
        
        for collection in collections_to_drop:
            try:
                self.client["readbuddy"].drop_collection(collection)
                print(f"✅ Dropped collection: {collection}")
            except Exception as e:
                print(f"❌ Failed to drop collection {collection}: {e}")
        
        print(f"Database cleanup completed. Dropped {len(collections_to_drop)} collections.")
    
    def _cleanup_expired_tokens(self, timeout: int = 300):
        """Remove expired confirmation tokens from database"""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout)  # 5 minutes ago
        self.random_components.delete_many({
            "created_at": {"$lt": cutoff.isoformat()}
        })
