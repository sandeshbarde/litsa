"""
LLM Hot-Training & In-Context Few-Shot Adaptation Engine.
Allows dynamic run-time prompt tuning, few-shot exemplar injection,
and persona hot-swapping without redeploying or retraining neural weights.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger


CONFIG_FILE = Path("data/hot_training_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "system_persona": (
        "You are an elite B2B Enterprise Web Architect and Digital Conversion Specialist representing Sandesh Barde. "
        "Your mission is to reach out to CEOs, Founders, and Managing Directors of wholesale, trade, and commercial businesses "
        "that currently have NO official website. You identify their exact digital revenue leak, calculate their lost revenue, "
        "and present a compelling, private live prototype website built specifically for them."
    ),
    "sales_tone": "Authoritative, ROI-focused, respectful, concise (under 120 words), zero fluff.",
    "key_differentiators": [
        "Private live interactive prototype prepared before reaching out",
        "Direct RFQ (Request for Quote) engine that stops customer leakage to competitors",
        "Full-Stack Web Architect based in India with global delivery track record"
    ],
    "winning_exemplars": [
        {
            "category": "Building Materials & Hardware",
            "loophole": "No digital catalog or RFQ portal; buyers switching to digital suppliers",
            "pitch_sample": (
                "Dear Leadership,\n\n"
                "While analyzing commercial hardware distributors in Dubai, we noticed that your firm operates without an active procurement portal. "
                "Regional contractors are increasingly placing bulk orders through suppliers with online RFQ systems, diverting an estimated $40,000+ in annual orders.\n\n"
                "We took the liberty of building a private, working prototype for your catalog with an automated quotation engine:\n"
                "👉 Live Concept: [PROTOTYPE_URL]\n\n"
                "Can we connect for 5 minutes this Thursday to review it?\n\n"
                "Best regards,\nSandesh Barde\nFull-Stack Web Architect (India)\nPortfolio: https://sandeshbarde.netlify.app/\nGitHub: https://github.com/sandeshbarde\nLinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
            )
        },
        {
            "category": "Auto Spare Parts & Trading",
            "loophole": "Relying strictly on phone calls with zero WhatsApp Web catalog for international GCC buyers",
            "pitch_sample": (
                "Dear Managing Director,\n\n"
                "In reviewing automotive spare parts distributors in your area, your competitors are capturing search traffic by offering instant WhatsApp-integrated part lookup. "
                "Without a digital catalog, high-margin export inquiries from regional buyers are being missed.\n\n"
                "We designed a luxury prototype showcasing your parts inventory, instant WhatsApp hotline, and corporate profile:\n"
                "👉 View Private Demo: [PROTOTYPE_URL]\n\n"
                "Would you be open to a quick 5-minute walkthrough?\n\n"
                "Best regards,\nSandesh Barde\nFull-Stack Web Architect (India)\nPortfolio: https://sandeshbarde.netlify.app/\nGitHub: https://github.com/sandeshbarde\nLinkedIn: https://www.linkedin.com/in/sandesh-barde-26ba3839b/"
            )
        }
    ]
}


class HotTrainingService:
    """Manages hot-tuning parameters and dynamically injects exemplars into LLM prompts."""

    def __init__(self):
        self.config_path = CONFIG_FILE
        self._load_config()

    def _load_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.config = DEFAULT_CONFIG.copy()
            self._save_config()
        else:
            try:
                self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load hot training config: {e}. Using defaults.")
                self.config = DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save hot training config: {e}")

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Hot-swap the prompt instructions or exemplars at runtime."""
        for k, v in updates.items():
            if k in self.config and v is not None:
                self.config[k] = v
        self._save_config()
        logger.info("Hot training configuration updated successfully.")
        return self.config

    def add_winning_exemplar(self, category: str, loophole: str, pitch_sample: str) -> None:
        """Add a newly closed / winning email pitch as training exemplar."""
        exemplar = {
            "category": category,
            "loophole": loophole,
            "pitch_sample": pitch_sample,
        }
        self.config.setdefault("winning_exemplars", []).append(exemplar)
        self._save_config()
        logger.info(f"New winning exemplar added for category: {category}")

    def build_hot_prompt_prefix(self) -> str:
        """Construct the dynamic system prompt with hot-trained rules and best exemplars."""
        persona = self.config.get("system_persona", "")
        tone = self.config.get("sales_tone", "")
        exemplars = self.config.get("winning_exemplars", [])

        exemplar_text = ""
        for idx, ex in enumerate(exemplars[:2], 1):
            exemplar_text += f"\n--- High-Converting Winning Example #{idx} ---\nIndustry: {ex.get('category')}\nIdentified Loophole: {ex.get('loophole')}\nPitch:\n{ex.get('pitch_sample')}\n"

        return (
            f"SYSTEM ROLE & PERSONA:\n{persona}\n\n"
            f"TONE & STYLE GUIDELINES:\n{tone}\n\n"
            f"FEW-SHOT WINNING TRAINING EXAMPLES:{exemplar_text}\n"
        )


hot_training_service = HotTrainingService()
