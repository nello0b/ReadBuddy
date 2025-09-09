# app/services/tts_interface.py

from abc import ABC, abstractmethod
from xml.etree.ElementTree import Element
from typing import List

class TTSService(ABC):
    @abstractmethod
    def synthesize_multi(self, 
                         ssml_chunks: List[Element], 
                         voice: str = "en-US-AriaNeural") -> List[str]:
        """
        Synthesizes speech for multiple SSML XML elements using the specified voice.

        Args:
            ssml_chunks (List[Element]): List of SSML XML elements representing input text and speech markup.
            voice (str): The voice to use for synthesis (default: 'en-US-AriaNeural').

        Returns:
            List[str]: List of paths to the generated audio files.
        """
        pass
