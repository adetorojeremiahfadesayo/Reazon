import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from src.config import (
    FORCE_MOCK_MODE,
    AZURE_AI_PROJECT_ENDPOINT,
    LearnerProfile,
    SYNTHETIC_DIR,
    DOCUMENTS_DIR
)
from src.connectors.graph_connector import MicrosoftGraphConnector

# Optional Azure AI Import
try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
except ImportError:
    AIProjectClient = None
    DefaultAzureCredential = None

class FoundryIQ:
    """
    Foundry IQ: Multi-source grounded knowledge retrieval.
    Toggles between Azure AI search query and local mock search against MD guides.
    """
    def __init__(self):
        self.use_azure = not FORCE_MOCK_MODE and AZURE_AI_PROJECT_ENDPOINT and AIProjectClient is not None
        self._local_docs_cache = {}

    def _get_local_doc_content(self, cert_id: str) -> str:
        filename = f"{cert_id.lower().replace('-', '')}_guide.md"
        path = os.path.join(DOCUMENTS_DIR, filename)
        if path in self._local_docs_cache:
            return self._local_docs_cache[path]
        
        if not os.path.exists(path):
            return ""
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            self._local_docs_cache[path] = content
            return content

    def search_knowledge(self, query: str, cert_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves relevant grounded document blocks containing citations.
        """
        if self.use_azure:
            try:
                # Live implementation would retrieve from active Azure search index connection
                # client = AIProjectClient(endpoint=AZURE_AI_PROJECT_ENDPOINT, credential=DefaultAzureCredential())
                # For safety and speed, we implement a fallback inside live mode too
                pass
            except Exception as e:
                print(f"[Foundry IQ] Azure retrieval error: {e}. Falling back to local search.")

        # Local search implementation (Regex & Keyword Match)
        content = self._get_local_doc_content(cert_id)
        if not content:
            return []

        # Split content by markdown domain sections
        sections = content.split("---")
        results = []
        
        keywords = [w.lower() for w in query.split() if len(w) > 3]
        for sec in sections:
            score = 0
            sec_lower = sec.lower()
            for kw in keywords:
                if kw in sec_lower:
                    score += 1
            if score > 0 or not keywords:  # If keywords match or empty query
                # Extract citation tags like [Ref: AI102-D1-SEC] or [Citation: ...]
                citation = "Unknown"
                ref_match = re.search(r'\[Ref:\s*([A-Za-z0-9-]+)\]', sec)
                if ref_match:
                    citation = f"[Ref: {ref_match.group(1)}]"
                
                results.append({
                    "text": sec.strip(),
                    "score": score,
                    "citation": citation
                })
                
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:3]

class FabricIQ:
    """
    Fabric IQ: Semantic foundation mapping business ontology.
    Validates business rules, prerequisites, and organizational roles.
    """
    def __init__(self):
        self.certifications_path = os.path.join(SYNTHETIC_DIR, "certifications.json")
        self.resources_path = os.path.join(SYNTHETIC_DIR, "learn_resources.json")
        self.certs_cache = []
        self.resources_cache = {}
        self._load_ontology()

    def _load_ontology(self):
        if os.path.exists(self.certifications_path):
            try:
                with open(self.certifications_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.certs_cache = data.get("certifications", [])
                if os.path.exists(self.resources_path):
                    with open(self.resources_path, "r", encoding="utf-8") as f:
                        self.resources_cache = json.load(f).get("resources", {})
            except Exception as e:
                print(f"[Fabric IQ] Error loading ontology: {e}")

    def get_certification(self, cert_id: str) -> Optional[Dict[str, Any]]:
        for c in self.certs_cache:
            if c["id"] == cert_id:
                return c
        return None

    def get_learning_resource(self, cert_id: str, domain_name: str = "") -> Dict[str, Any]:
        resource = self.resources_cache.get(cert_id, {})
        if not resource:
            query = cert_id if not domain_name else f"{cert_id}%20{domain_name.replace(' ', '%20')}"
            return {
                "certification_url": "https://learn.microsoft.com/en-us/credentials/certifications/",
                "learn_path_url": f"https://learn.microsoft.com/en-us/training/browse/?terms={query}",
                "resource_title": f"{cert_id} Microsoft Learn resources"
            }

        courses = resource.get("courses", [])
        if not courses:
            return resource

        domain_lower = domain_name.lower()
        best_course = courses[0]
        best_score = -1
        domain_terms = {term for term in re.findall(r"[a-z0-9]+", domain_lower) if len(term) > 3}

        for course in courses:
            match_text = str(course.get("match", "")).lower()
            title_text = str(course.get("resource_title", "")).lower()
            score = 0
            if match_text and (match_text in domain_lower or domain_lower in match_text):
                score += 10
            score += len(domain_terms.intersection(re.findall(r"[a-z0-9]+", f"{match_text} {title_text}")))
            if score > best_score:
                best_course = course
                best_score = score

        return {
            **resource,
            "learn_path_url": best_course.get("resource_url", resource.get("learn_path_url")),
            "resource_title": best_course.get("resource_title", resource.get("resource_title", "Microsoft Learn course")),
            "resource_match": best_course.get("match", domain_name)
        }

    def validate_prerequisites(self, profile: LearnerProfile) -> Tuple[bool, str]:
        """
        Check if the learner has met the prerequisite certification path.
        """
        cert = self.get_certification(profile.certification_target)
        if not cert:
            return False, f"Certification {profile.certification_target} not found in ontology."
            
        prereqs = cert.get("prerequisites", [])
        if not prereqs:
            return True, "No prerequisites required."

        # Simplistic verification: if profile indicates they already hold the prereq
        # (For simulation, we check if their role aligns or they pass a check)
        if profile.exam_outcome == "Pass" and profile.certification_target in prereqs:
            return True, "Prerequisites completed."
            
        # If their role aligns with DevOps and they are attempting AZ-400
        if profile.certification_target == "AZ-400":
            # Check if they have cloud background or completed AZ-104
            if "Cloud Engineer" in profile.role or "Architect" in profile.role:
                return True, "Prerequisites satisfied via professional experience."
            return False, "Warning: AZ-400 requires Azure administration experience. Please complete AZ-104 path first."

        return True, "Prerequisites check passed."

    def get_role_alignment(self, role: str) -> List[str]:
        """
        Suggests relevant certification paths based on employee role.
        """
        role_lower = role.lower()
        if "security" in role_lower:
            return ["SC-900", "SC-300", "AZ-500"]
        elif "power bi" in role_lower or "analyst" in role_lower:
            return ["DP-900", "PL-300"]
        elif "power platform" in role_lower or "automation" in role_lower:
            return ["PL-900", "PL-200"]
        elif "sales" in role_lower or "revenue" in role_lower or "customer" in role_lower:
            return ["MB-800"]
        elif "microsoft 365" in role_lower or "workplace" in role_lower:
            return ["MS-900", "MS-102"]
        elif "architect" in role_lower:
            return ["AZ-900", "AZ-104", "AZ-305"]
        elif "operations" in role_lower or "administrator" in role_lower:
            return ["AZ-900", "AZ-104"]
        elif "ai" in role_lower:
            return ["AI-901", "AI-200"]
        elif "data" in role_lower:
            return ["DP-900", "DP-600", "DP-700"]
        elif "founder" in role_lower or "startup" in role_lower:
            return ["AZ-900", "AI-901", "SC-900", "MS-900"]
        elif "devops" in role_lower or "sre" in role_lower:
            return ["AZ-104", "AZ-400"]
        elif "cloud" in role_lower or "developer" in role_lower:
            return ["AZ-900", "AI-200"]
        else:
            return ["AZ-900", "AI-901"]  # Default entry path

class WorkIQ:
    """
    Work IQ: Real-time work context analysis.
    Interprets calendar load and meeting frequency to adjust capacity.
    """
    def __init__(self):
        self.work_signals_path = os.path.join(SYNTHETIC_DIR, "work_signals.json")
        self.graph = MicrosoftGraphConnector()
        self.signals_cache = []
        self._load_signals()

    def _load_signals(self):
        if os.path.exists(self.work_signals_path):
            try:
                with open(self.work_signals_path, "r", encoding="utf-8") as f:
                    self.signals_cache = json.load(f)
            except Exception as e:
                print(f"[Work IQ] Error loading work signals: {e}")

    def get_signals_by_employee(self, employee_id: str) -> Dict[str, Any]:
        graph_signals = self.graph.get_work_signals(employee_id)
        if graph_signals:
            return graph_signals
        for s in self.signals_cache:
            if s["employee_id"] == employee_id:
                return s
        # Return sensible default signals
        return {
            "employee_id": employee_id,
            "meeting_hours_per_week": 15,
            "focus_hours_per_week": 15,
            "preferred_learning_slot": "Morning",
            "weekly_study_budget_hours": 5
        }

    def evaluate_burnout_risk(self, employee_id: str) -> Tuple[str, str]:
        """
        Determines meeting overload status and risk tier.
        """
        sig = self.get_signals_by_employee(employee_id)
        meetings = sig.get("meeting_hours_per_week", 15)
        focus = sig.get("focus_hours_per_week", 15)

        if meetings > 25:
            return "High", f"Critical meeting load ({meetings} hrs/wk). High risk of context-switching burnout."
        elif meetings > 18:
            return "Medium", f"Elevated meeting load ({meetings} hrs/wk). Restrict study sessions to focus blocks."
        else:
            return "Low", f"Healthy calendar ratio. {focus} focus hours available for learning execution."
