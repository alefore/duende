from abc import ABC, abstractmethod
from typing import Optional

class ConfirmationManager(ABC):

    @abstractmethod
    def RequireConfirmation(self, message: str) -> Optional[str]:
        """Blocks execution until confirmation is given, returning additional guidance if provided by the user."""
        pass
        
class CLIConfirmationManager(ConfirmationManager):

    def RequireConfirmation(self, message: str) -> Optional[str]:
        print(message)
        return input(
            "Confirm operations? Enter a message to provide guidance to the AI: "
        ).strip()