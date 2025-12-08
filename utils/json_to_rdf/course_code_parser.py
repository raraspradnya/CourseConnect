"""
Course Code Parser - Detects and normalizes course codes from text

Handles formats like:
- "COMPSCI 61A and 61B" → ["CS 61A", "CS 61B"]
- "CS 61A and 61B" → ["CS 61A", "CS 61B"]  
- "INFO 206B or equivalent" → ["INFO 206B"]
- "CS C100/DATA C100/STAT C100" → ["CS C100", "DATA C100", "STAT C100"]
"""

import re
from typing import List, Dict, Tuple, Optional

class CourseCodeParser:
    """Parse and normalize course codes from prerequisite text"""
    
    def __init__(self):
        """
        Initialize parser
        
        Args:
            graph: Optional RDF graph to validate course codes against
        """
        
        # Department abbreviation mappings (short → full)
        self.dept_aliases = {
            'COMPSCI': 'CS',
            'STATISTICS': 'STAT'
        }
        
    def parse_prerequisite_text(self, text: str) -> Dict:
        """
        Parse prerequisite text and extract course codes
        
        Args:
            text: Prerequisite text (e.g., "COMPSCI 61A and 61B. Strong programming skills.")
            
        Returns:
            Dictionary with parsed courses, logic, and remainder text
        """
        # Normalize text
        normalized_text = text.upper().strip()
        # Extract all course codes
        courses = self.extract_course_codes(normalized_text)
        
        # Detect logical relationships
        has_and = ' AND ' in normalized_text or '&' in normalized_text
        has_or = ' OR ' in normalized_text or '/' in normalized_text
        
        # Determine primary logic
        if has_and and has_or:
            logic = 'COMPLEX'
        elif has_and:
            logic = 'AND'
        elif has_or:
            logic = 'OR'
        else:
            logic = 'SINGLE' if len(courses) == 1 else 'UNKNOWN'
        
        # Extract non-course requirements (skills, experience, etc.)
        remainder = self._extract_remainder(normalized_text, courses)
        
        return {
            'courses': courses,
            'logic': logic,
            'has_equivalents': 'EQUIVALENT' in normalized_text,
            'remainder_text': remainder,
            'original_text': text
        }
    
    def extract_course_codes(self, text: str) -> List[Dict]:
        """
        Extract all course codes from text
        
        Args:
            text: Text to parse
            
        Returns:
            List of course dictionaries with normalized codes
        """
        courses = []
        text = text.upper()
        
        # Pattern 1: Full format "COMPSCI 61A", "INFO 206B"
        # Matches: DEPT### or DEPT###X or DEPT C### (for cross-listed)
        full_pattern = r'\b([A-Z]+)\s+([C]?[0-9]+[A-Z]?)\b'
        
        for match in re.finditer(full_pattern, text):
            dept = match.group(1)
            number = match.group(2).replace(' ', '')  # Remove spaces from "C 100"
            
            # Skip if department is a logical connector, but use previous department
            if dept in ('AND', 'OR'):
                if courses:  # Use the last extracted department
                    dept = courses[-1]['department']
                else:
                    continue
            
            # Normalize department
            dept_normalized = self.dept_aliases.get(dept, dept)
            
            course_code = f"{dept_normalized} {number}"
            courses.append({
            'course_code': course_code,
            'department': dept_normalized,
            'number': number,
            'original_match': match.group(0)
            })
        
        # Pattern 2: Abbreviated format "61A and 61B" (inherit department from context)
        # This requires looking at the last full course code mentioned
        abbreviated_pattern = r'(and|or|,|&|/)\s+([C]?[0-9]+[A-Z]?)\b'
        
        last_dept = None
        for course in courses:
            last_dept = course['department']
        
        if last_dept:
            for match in re.finditer(abbreviated_pattern, text):
                number = match.group(2)
                course_code = f"{last_dept} {number}"
                
                # Check if we haven't already captured this
                if not any(c['course_code'] == course_code for c in courses):
                    courses.append({
                        'course_code': course_code,
                        'department': last_dept,
                        'number': number,
                        'original_match': match.group(2),
                        'inherited_dept': True
                    })
        
        # Pattern 3: Slash-separated cross-listed courses "COMPSCI C100/DATA C100/STAT C100"
        
        slash_pattern = r'(?:[A-Z]+\s+[C]?[0-9]+[A-Z]?\s*/\s*)+[A-Z]+\s+[C]?[0-9]+[A-Z]?' 
        
        for match in re.finditer(slash_pattern, text):
            # Split by slash and parse each
            parts = match.group(0).split('/')
            for part in parts:
                part = part.strip()
                dept_match = re.match(r'([A-Z]+)\s+([C]?[0-9]+[A-Z]?)', part)
                if dept_match:
                    dept = self.dept_aliases.get(dept_match.group(1), dept_match.group(1))
                    number = dept_match.group(2)
                    course_code = f"{dept} {number}"
                    if not any(c['course_code'] == course_code for c in courses):
                        courses.append({
                            'course_code': course_code,
                            'department': dept,
                            'number': number,
                            'original_match': part,
                            'cross_listed': True
                        })
                    else:
                        # Mark existing entry as cross-listed
                        for c in courses:
                            if c['course_code'] == course_code:
                                c['cross_listed'] = True
        
        return courses
    
    
    def _extract_remainder(self, text: str, courses: List[Dict]) -> Optional[str]:
        """Extract non-course requirement text (skills, experience, etc.)"""
        
        # Remove all course mentions
        remainder = text
        for course in courses:
            remainder = remainder.replace(course['original_match'], '')
        
        # Remove logical connectors
        remainder = re.sub(r'\b(AND|OR|WITH)\b', '', remainder)
        
        # Remove grade requirements
        remainder = re.sub(r'\b[A-D][+-]?\s+OR\s+BETTER\b', '', remainder)
        remainder = re.sub(r'\bMINIMUM GRADE[^.]*\b', '', remainder)
        
        # Remove common punctuation
        remainder = re.sub(r'[,;/]', '', remainder)
        
        # Clean up whitespace
        remainder = ' '.join(remainder.split())
        remainder = remainder.strip('. ')
        
        # If there's something substantial left, return it
        if len(remainder) > 10:  # Arbitrary threshold
            return remainder
        
        return None
 
    def normalize_course_code(self, code: str) -> str:
        """
        Normalize a course code to standard format
        
        Args:
            code: Course code in any format
            
        Returns:
            Normalized course code (e.g., "COMPSCI 61A")
        """
        code = code.upper().strip()
        
        # Extract department and number
        match = re.match(r'([A-Z]+)\s*([0-9]+[A-Z]?)', code)
        if not match:
            return code
        
        dept = self.dept_aliases.get(match.group(1), match.group(1))
        number = match.group(2)
        
        return f"{dept} {number}"


# Example usage and tests
if __name__ == "__main__":
    
    # Initialize parser
    parser = CourseCodeParser()
    
    # Test cases
    test_cases = [
        "COMPSCI 61A and 61B. Strong programming skills.",
        "Recommended: Info 213, Info C262, Info 215",
        "INFO 206A & 206B",
        "COMPSCI 61B; COMPSCI 70, COMPSCI C100 / STAT C100 / DATA C100, MATH 55, STAT 134 or STAT C140 / DATA C140; strong programming skills.",
        "INFO 206B or equivalent college-level course in computer science in Python with a C- or better AND COMPSCI C100/DATA C100/STAT C100 or COMPSCI 189 or INFO 251 or DATA 144 or equivalent college-level course in data science with a C- or better.",
        "Computer Science 61B; Computer Science 70, Math 55, Statistics 134 or Statistics 140; strong programming skills"
    ]
    
    print("="*80)
    print("COURSE CODE PARSER - TEST RESULTS")
    print("="*80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Test: '{test}'")
        print("-" * 80)
        
        result = parser.parse_prerequisite_text(test)
        
        print(f"   Detected courses: {len(result['courses'])}")
        for course in result['courses']:
            inherited = " (inherited dept)" if course.get('inherited_dept') else ""
            cross = " [cross-listed]" if course.get('cross_listed') else ""
            print(f"      • {course['course_code']}{inherited}{cross}")
        
        print(f"   Logic: {result['logic']}")
        print(f"   Has equivalents: {result['has_equivalents']}")
        
        if result['remainder_text']:
            print(f"   Other requirements: {result['remainder_text']}")
    
    # Test normalization
    print("\n" + "="*80)
    print("NORMALIZATION TESTS")
    print("="*80)
    
    normalize_tests = ["CS61A", "cs 61a", "COMPSCI61A", "INFO206B", "DATA C100"]
    
    for code in normalize_tests:
        normalized = parser.normalize_course_code(code)
        print(f"   {code:15s} → {normalized}")
    
    print("\n" + "="*80)
    print("✅ PARSER READY")
    print("="*80)