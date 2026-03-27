"""
Dialogue generator for creating realistic OCC conversations.

Generates synthetic operator-dispatcher dialogue from templates and
incident context with slot filling, variation, and action annotation.
"""

import random
import re
from typing import Any, Optional
import string

from occlm.synthesis.templates.occ_conversations import (
    ConversationTemplate,
    DialogueTurn,
    CONVERSATION_TEMPLATES,
)

__all__ = [
    "DialogueGenerator",
]


class DialogueGenerator:
    """
    Generates synthetic OCC dialogue from templates and scenarios.

    Fills templates with incident context, varies formality level,
    generates alternatives, and annotates with actions.
    """

    def __init__(self, random_seed: Optional[int] = None) -> None:
        """
        Initialize dialogue generator.

        Args:
            random_seed: Optional seed for reproducibility
        """
        if random_seed is not None:
            random.seed(random_seed)

    def generate_occ_dialogue(
        self,
        scenario: dict[str, Any],
        difficulty: Optional[str] = None,
        template_name: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        """
        Generate complete OCC dialogue from scenario.

        Args:
            scenario: Scenario dict with incident_details, timestamp, etc.
            difficulty: Override difficulty (easy, medium, hard)
            template_name: Optional specific template to use

        Returns:
            List of dialogue messages with annotations
        """
        incident_type = (
            scenario.get("incident_details", {}).get("type")
        )
        if not incident_type:
            raise ValueError("scenario missing incident_details.type")

        # Find appropriate template
        if template_name:
            template = CONVERSATION_TEMPLATES.get(template_name)
        else:
            template = self._select_template(incident_type, difficulty)

        if not template:
            raise ValueError(
                f"No template found for {incident_type}"
            )

        # Generate dialogue from template
        dialogue = []
        for turn in template.turns:
            filled_message = self._slot_fill_template(
                turn.message,
                scenario,
            )

            # Vary formality
            varied_message = self._vary_formality(
                filled_message,
                template.difficulty,
            )

            message_dict = {
                "role": turn.speaker,
                "content": varied_message,
                "speaker": turn.speaker,
                "turn_number": len(dialogue) + 1,
                "template_used": template.name,
                "actions": turn.actions,
            }

            dialogue.append(message_dict)

        # Add alternatives for each message
        dialogue_with_alts = (
            self.annotate_dialogue_with_actions(dialogue)
        )

        return dialogue_with_alts

    def _select_template(
        self,
        incident_type: str,
        difficulty: Optional[str] = None,
    ) -> Optional[ConversationTemplate]:
        """
        Select appropriate template for incident.

        Args:
            incident_type: Type of incident
            difficulty: Optional difficulty override

        Returns:
            Selected ConversationTemplate or None
        """
        incident_templates = {
            "signal_failure": "signal_failure_response",
            "medical_emergency": "medical_emergency_response",
            "passenger_incident": "delay_escalation",
            "crowding": "crowd_management",
            "equipment_failure": "system_restart",
            "weather_related": "weather_response",
            "security_incident": "security_incident_response",
            "system_error": "system_restart",
        }

        template_name = incident_templates.get(
            incident_type,
            "delay_escalation",
        )
        return CONVERSATION_TEMPLATES.get(template_name)

    def _slot_fill_template(
        self,
        template: str,
        context: dict[str, Any],
    ) -> str:
        """
        Fill template slots with context values.

        Replaces {{key}} production-values with values from context.

        Args:
            template: Template string with {{production-value}} slots
            context: Dict with values to fill

        Returns:
            Filled template string
        """
        result = template
        incident = context.get("incident_details", {})

        # Build flat context dict
        flat_context = {
            **context,
            **incident,
        }

        # Find all production-values
        production-value_pattern = r"\{\{(\w+)\}\}"
        production-values = re.findall(production-value_pattern, result)

        for production-value in production-values:
            value = flat_context.get(production-value, f"{{{{unknown}}}}")

            # Generate reasonable values for common slots
            if production-value == "num_trains_bunched" and value == "{{unknown}}":
                value = random.randint(2, 5)
            elif production-value == "trains_affected" and value == "{{unknown}}":
                value = random.randint(2, 8)
            elif production-value == "affected_tracks" and value == "{{unknown}}":
                value = random.choice(["northbound", "southbound", "both"])
            elif production-value == "signal_location" and value == "{{unknown}}":
                value = f"Signal {random.randint(1, 100)}"
            elif production-value == "start_station" and value == "{{unknown}}":
                value = f"Station {random.choice(string.ascii_uppercase)}"
            elif production-value == "end_station" and value == "{{unknown}}":
                value = f"Station {random.choice(string.ascii_uppercase)}"
            elif production-value == "maintainer_eta" and value == "{{unknown}}":
                value = random.randint(10, 45)
            elif production-value == "estimated_repair_minutes" and value == "{{unknown}}":
                value = random.randint(15, 120)
            elif production-value == "short_turn_before" and value == "{{unknown}}":
                value = f"Station {random.choice(string.ascii_uppercase)}"
            elif production-value == "short_turn_after" and value == "{{unknown}}":
                value = f"Station {random.choice(string.ascii_uppercase)}"
            elif production-value == "line_id" and value == "{{unknown}}":
                value = random.choice(["1", "2", "3", "A", "B"])

            result = result.replace(
                f"{{{{{production-value}}}}}",
                str(value),
            )

        return result

    def _vary_formality(
        self,
        message: str,
        difficulty: str,
    ) -> str:
        """
        Vary formality level based on difficulty.

        Easy: clear, formal messages
        Medium: some colloquialisms, ambiguity
        Hard: radio jargon, efficiency focus, complexity

        Args:
            message: Base message to vary
            difficulty: Difficulty level

        Returns:
            Varied message string
        """
        if difficulty == "easy":
            # Keep formal, clear
            return message

        elif difficulty == "medium":
            # Add minor variations
            variations = [
                ("please ", ""),  # Remove some politeness
                ("thank you", "thanks"),
                ("would you", "can you"),
                ("understand", "copy"),
            ]

            result = message
            if random.random() < 0.3:
                old_text, new_text = random.choice(variations)
                if old_text in result:
                    result = result.replace(old_text, new_text, 1)

            return result

        else:  # hard
            # More radio jargon and efficiency
            variations = [
                ("please ", ""),
                ("thank you", ""),
                ("understood", "copy"),
                ("would you ", ""),
                ("can you ", ""),
                ("approximately ", "approx "),
                ("signal problem", "signal issue"),
                ("currently", "now"),
                ("understand", "copy"),
                ("the", ""),  # Radio style
            ]

            result = message
            for old_text, new_text in variations:
                if random.random() < 0.2 and old_text in result:
                    result = result.replace(old_text, new_text, 1)

            # Add radio-style abbreviations
            if random.random() < 0.2:
                result = f"{result} (Over)" if "(Over)" not in result else result

            return result

    def _generate_alternatives(
        self,
        base_message: str,
        num: int = 3,
    ) -> list[str]:
        """
        Generate alternative phrasings of message.

        Args:
            base_message: Base message to create alternatives for
            num: Number of alternatives to generate

        Returns:
            List containing base_message plus alternatives
        """
        alternatives = [base_message]

        for _ in range(num):
            alt = base_message

            # Synonym substitutions
            synonyms = {
                "problem": ["issue", "situation", "trouble"],
                "delay": ["backup", "slowdown", "wait"],
                "hold": ["stop", "suspend", "wait"],
                "clear": ["open", "proceed", "go"],
                "resume": ["continue", "return to", "go back to"],
                "understood": ["copy", "acknowledged", "roger"],
                "error": ["fault", "malfunction", "failure"],
            }

            for word, alts in synonyms.items():
                if word in alt.lower():
                    new_word = random.choice(alts)
                    # Case-insensitive replacement
                    pattern = re.compile(
                        re.escape(word),
                        re.IGNORECASE,
                    )
                    alt = pattern.sub(new_word, alt, count=1)
                    break

            if alt != base_message:
                alternatives.append(alt)

        return alternatives[:num + 1]

    def annotate_dialogue_with_actions(
        self,
        dialogue: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        """
        Annotate dialogue messages with operational actions.

        Adds ground truth action annotations for training.

        Args:
            dialogue: List of dialogue message dicts

        Returns:
            Dialogue with added action annotations
        """
        annotated = []

        for message in dialogue:
            msg_copy = dict(message)

            # Add action alternatives
            if "actions" in msg_copy:
                action_list = msg_copy["actions"]
            else:
                action_list = self._infer_actions(msg_copy["content"])

            msg_copy["actions"] = action_list
            msg_copy["action_confidence"] = random.uniform(0.7, 0.95)

            # Add alternative phrasings
            alternatives = self._generate_alternatives(
                msg_copy["content"],
                num=2,
            )
            msg_copy["alternatives"] = alternatives[1:]  # Skip base

            # Add severity indicators for hard mode
            if "incident" in msg_copy.get("content", "").lower():
                msg_copy["has_urgency"] = True
            else:
                msg_copy["has_urgency"] = False

            # Add speaker role context
            if msg_copy["speaker"] == "operator":
                msg_copy["speaker_context"] = "field_operator"
            elif msg_copy["speaker"] == "dispatcher":
                msg_copy["speaker_context"] = "occ_dispatcher"
            else:
                msg_copy["speaker_context"] = msg_copy["speaker"]

            annotated.append(msg_copy)

        return annotated

    def _infer_actions(self, message: str) -> list[str]:
        """
        Infer operational actions from message content.

        Args:
            message: Message to infer actions from

        Returns:
            List of inferred actions
        """
        actions = []
        message_lower = message.lower()

        action_keywords = {
            "incident_detection": ["detected", "incident", "failure", "emergency"],
            "status_report": ["running", "delay", "affected", "report"],
            "status_update": ["update", "minutes", "status", "currently"],
            "hold_decision": ["hold", "holding", "suspend", "stop"],
            "short_turn": ["short turn", "shorten", "turn back"],
            "communication": [
                "notify", "announce", "inform", "communicate"
            ],
            "monitoring": [
                "monitor", "watch", "continue", "maintain"
            ],
            "emergency_services_alert": [
                "ems", "police", "emergency", "dispatch"
            ],
            "service_resume": [
                "resume", "proceed", "clear", "go"
            ],
        }

        for action, keywords in action_keywords.items():
            if any(kw in message_lower for kw in keywords):
                actions.append(action)

        if not actions:
            actions.append("communication")

        return actions[:3]  # Return up to 3 actions
