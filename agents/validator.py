"""
Complete example demonstrating prerequisite chain mapping with missing course handling

This example shows:
1. How to create a TTL file with missing prerequisites
2. How the system handles missing courses gracefully
3. How to generate reports and stubs for missing courses
4. How the CrewAI agent communicates issues to students
"""

# Example TTL data with missing prerequisites
EXAMPLE_TTL = """
@prefix ex: <http://example.org/> .
@prefix schema: <http://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# INFO 253A - Fully defined course
ex:INFO253A a schema:Course ;
    schema:courseCode "INFO 253A"^^xsd:string ;
    schema:name "Front-End Web Architecture"^^xsd:string ;
    schema:numberOfCredits 3 ;
    ex:hasTopics "JavaScript"^^xsd:string, "React"^^xsd:string, "HTML"^^xsd:string ;
    ex:offeredIn ex:INFO253A_Fall2025 .

ex:INFO253A_Fall2025 a ex:CourseOffering ;
    ex:semester "2025 Fall"^^xsd:string ;
    ex:hasComponent ex:INFO253A_Fall2025_LEC_0 .

ex:INFO253A_Fall2025_LEC_0 a ex:LectureComponent ;
    ex:componentType "Lecture" ;
    ex:instructor "Kay Ashaolu"^^xsd:string ;
    ex:hasTimeSlot ex:INFO253A_Fall2025_LEC_0_Slot .

ex:INFO253A_Fall2025_LEC_0_Slot a ex:TimeSlot ;
    ex:dayOfWeek ex:Monday ;
    ex:startTime "09:00:00"^^xsd:time ;
    ex:endTime "11:00:00"^^xsd:time ;
    ex:startMinutes 540 ;
    ex:endMinutes 660 ;
    ex:location "210 South Hall" .

# INFO 206B - Has prerequisites, some missing
ex:INFO206B a schema:Course ;
    schema:courseCode "INFO 206B"^^xsd:string ;
    schema:name "Distributed Computing"^^xsd:string ;
    schema:numberOfCredits 3 ;
    ex:hasPrerequisite ex:INFO206A ;  # This one is defined
    ex:hasPrerequisite ex:CS101 ;     # This one is MISSING
    ex:offeredIn ex:INFO206B_Fall2025 .

ex:INFO206B_Fall2025 a ex:CourseOffering ;
    ex:semester "2025 Fall"^^xsd:string .

# INFO 206A - Defined, but has a missing prerequisite
ex:INFO206A a schema:Course ;
    schema:courseCode "INFO 206A"^^xsd:string ;
    schema:name "Introduction to Computing"^^xsd:string ;
    schema:numberOfCredits 3 ;
    ex:hasPrerequisite ex:MATH101 ;   # This one is MISSING
    ex:offeredIn ex:INFO206A_Spring2025 .

ex:INFO206A_Spring2025 a ex:CourseOffering ;
    ex:semester "2025 Spring"^^xsd:string .

# Note: CS101 and MATH101 are referenced but NOT defined as Course objects
"""


def create_example_ttl_file(filename: str = "example_courses.ttl"):
    """Create an example TTL file for testing"""
    with open(filename, 'w') as f:
        f.write(EXAMPLE_TTL)
    print(f"✅ Created example TTL file: {filename}")
    return filename


def demonstrate_missing_course_handling():
    """Main demonstration"""
    from graph_query_tool import GraphQueryTool
    from missing_course_utils import MissingCourseManager
    
    print("="*80)
    print("DEMONSTRATION: Handling Missing Prerequisites")
    print("="*80)
    print()
    
    # Step 1: Create example data
    ttl_file = create_example_ttl_file()
    
    # Step 2: Initialize tools
    print("\n📊 Initializing graph query tool...")
    tool = GraphQueryTool(ttl_file)
    manager = MissingCourseManager(tool)
    
    # Step 3: Analyze INFO 206B (has missing prerequisites)
    print("\n" + "="*80)
    print("ANALYZING: INFO 206B")
    print("="*80)
    
    print("\n1. Get course info:")
    info = tool.get_course_info("INFO 206B")
    print(f"   Name: {info['name']}")
    print(f"   Credits: {info['credits']}")
    
    print("\n2. Get full prerequisite chain:")
    chain = tool.get_full_prerequisite_chain("INFO 206B")
    import json
    print(json.dumps(chain, indent=2))
    
    print("\n3. Get flat prerequisite list:")
    flat = tool.get_all_prerequisites_flat("INFO 206B")
    print(f"   Defined prerequisites: {flat['defined']}")
    print(f"   Missing prerequisites: {flat['missing']}")
    print(f"   ⚠️  Warning: {len(flat['missing'])} prerequisite(s) are not fully defined")
    
    print("\n4. Calculate minimum semesters:")
    semesters = tool.calculate_minimum_semesters("INFO 206B")
    print(f"   Minimum semesters: {semesters['minimum_semesters']}")
    if semesters.get('warning_message'):
        print(f"   ⚠️  {semesters['warning_message']}")
    
    print("\n5. Get prerequisite paths:")
    paths = tool.get_prerequisite_paths("INFO 206B")
    print(f"   Found {paths['path_count']} path(s)")
    if paths['warnings']:
        print(f"   ⚠️  Warnings: {paths['warnings']}")
    for i, path in enumerate(paths['paths'], 1):
        print(f"   Path {i}: {' -> '.join(path)}")
    
    # Step 4: Generate system-wide report
    print("\n" + "="*80)
    print("SYSTEM-WIDE ANALYSIS")
    print("="*80)
    print(manager.generate_missing_course_report())
    
    # Step 5: Validate specific course
    print("\n" + "="*80)
    print("VALIDATION CHECK")
    print("="*80)
    validation = manager.validate_prerequisite_integrity("INFO 206B")
    print(f"\nValidating INFO 206B:")
    print(f"  ✓ Valid: {validation['is_valid']}")
    print(f"  ✓ Total issues: {validation['total_issues']}")
    print(f"  ✓ Missing courses: {validation['missing_courses']}")
    if validation['issues']:
        print("\n  Issues found:")
        for issue in validation['issues']:
            print(f"    • {issue}")
    
    # Step 6: Generate stub file
    print("\n" + "="*80)
    print("GENERATING STUB FILE")
    print("="*80)
    result = manager.create_stub_ttl_for_missing_courses()
    print(result)
    
    # Step 7: Show how the agent would respond
    print("\n" + "="*80)
    print("HOW THE AGENT RESPONDS TO STUDENTS")
    print("="*80)
    print("""
When a student asks: "What's the full prerequisite chain for INFO 206B?"

The agent will respond something like:

---
Great question! Let me analyze INFO 206B (Distributed Computing) for you.

📚 Course Overview:
- Name: Distributed Computing
- Credits: 3

📋 Prerequisite Requirements:
To take INFO 206B, you need to complete:

1. INFO 206A (Introduction to Computing) ✅
   - This is fully defined in our system
   - It requires: MATH 101 ⚠️

2. CS 101 ⚠️
   - This course is listed as a prerequisite but not fully defined in our knowledge graph
   - This might be an external prerequisite from another department

⚠️ Important Notes:
- Some prerequisites (CS 101, MATH 101) are referenced but not fully defined in our system
- These may be courses from other departments or prerequisites that haven't been added yet
- I recommend checking with your academic advisor to confirm the exact requirements for these courses

⏱️ Timeline:
Based on the longest prerequisite chain, you'll need a minimum of 3 semesters to reach INFO 206B
(assuming you take one prerequisite per semester).

💡 Recommendation:
Before planning to take INFO 206B, please verify the requirements for CS 101 and MATH 101 with 
your advisor, as these courses aren't fully tracked in our current system.

Would you like me to help you find more information about any of these prerequisites?
---
""")


if __name__ == "__main__":
    demonstrate_missing_course_handling()
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nKey Takeaways:")
    print("1. The system gracefully handles missing prerequisite courses")
    print("2. It clearly marks which courses are missing vs. defined")
    print("3. It provides warnings but continues to function")
    print("4. It can generate reports and stubs to help complete the knowledge graph")
    print("5. The agent communicates these limitations clearly to students")