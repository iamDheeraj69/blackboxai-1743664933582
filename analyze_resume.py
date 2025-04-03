import json
import re
from typing import Dict, List
from pathlib import Path

class ResumeAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_type = Path(file_path).suffix.lower()
        self.text_content = ""
        self.analysis_results = {
            "score": 0,
            "skills": [],
            "experience": [],
            "suggestions": []
        }

    def extract_text(self) -> None:
        """Extract text content based on file type"""
        try:
            if not os.path.exists(self.file_path):
                raise Exception(f"File not found: {self.file_path}")
                
            if self.file_type == '.pdf':
                import PyPDF2
                with open(self.file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    self.text_content = "\n".join(
                        [page.extract_text() for page in reader.pages if page.extract_text()]
                    )
                    if not self.text_content.strip():
                        raise Exception("PDF contains no extractable text - may be image-based")
            elif self.file_type == '.docx':
                import docx
                doc = docx.Document(self.file_path)
                self.text_content = "\n".join(
                    [para.text for para in doc.paragraphs]
                )
            else:  # Assume plain text
                with open(self.file_path, 'r') as file:
                    self.text_content = file.read()
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")

    def analyze_skills(self) -> None:
        """Analyze and extract skills from resume text"""
        # Placeholder - in a real implementation, use NLP or pattern matching
        common_skills = [
            "JavaScript", "Python", "Java", "C++", "React", 
            "Node.js", "SQL", "AWS", "Docker", "Git"
        ]
        
        found_skills = []
        for skill in common_skills:
            if re.search(rf'\b{skill}\b', self.text_content, re.IGNORECASE):
                found_skills.append({
                    "name": skill,
                    "strength": min(100, len(re.findall(rf'\b{skill}\b', self.text_content, re.IGNORECASE)) * 20)
                })
        
        self.analysis_results["skills"] = found_skills

    def analyze_experience(self) -> None:
        """Analyze work experience section"""
        # Placeholder - in a real implementation, use more sophisticated parsing
        experience_pattern = r'(?P<title>[A-Z][a-z]+(?: [A-Z][a-z]+)*)\s*at\s*(?P<company>[A-Z][a-zA-Z0-9& ]+)\s*\((?P<duration>\d{4}\s*-\s*(?:Present|\d{4}))\)'
        matches = re.finditer(experience_pattern, self.text_content)
        
        self.analysis_results["experience"] = [
            {
                "title": m.group('title'),
                "company": m.group('company'),
                "duration": m.group('duration'),
                "description": "Extracted from resume"  # Placeholder
            }
            for m in matches
        ][:5]  # Limit to 5 most recent

    def generate_suggestions(self) -> None:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Check for quantifiable achievements
        if not re.search(r'\d+%|\$\d+|\d+\+', self.text_content):
            suggestions.append("Add more quantifiable achievements (e.g., 'Increased performance by 30%')")
            
        # Check for action verbs
        action_verbs = ['developed', 'implemented', 'led', 'managed', 'created']
        if not any(verb in self.text_content.lower() for verb in action_verbs):
            suggestions.append("Use more action verbs (e.g., 'Developed', 'Implemented', 'Led')")
            
        self.analysis_results["suggestions"] = suggestions[:3]  # Limit to 3 suggestions

    def calculate_score(self) -> None:
        """Calculate overall resume score"""
        base_score = 5.0
        
        # Add points for skills
        base_score += min(3, len(self.analysis_results["skills"]) * 0.5)
        
        # Add points for experience
        base_score += min(2, len(self.analysis_results["experience"]) * 0.4)
        
        self.analysis_results["score"] = round(base_score, 1)

    def analyze(self) -> Dict:
        """Main analysis workflow"""
        self.extract_text()
        self.analyze_skills()
        self.analyze_experience()
        self.generate_suggestions()
        self.calculate_score()
        return self.analysis_results

if __name__ == "__main__":
    # Example usage
    analyzer = ResumeAnalyzer("sample_resume.pdf")
    results = analyzer.analyze()
    print(json.dumps(results, indent=2))