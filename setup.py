"""
Setup and initialization script for HR Agent MCP project.
Handles document ingestion, database setup, and initial configuration.
"""

import os
import sys
from pathlib import Path
import logging
import json
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_hr_documents():
    """Create sample HR documents for testing."""
    logger.info("Creating sample HR documents...")
    
    hr_docs_dir = project_root / "data" / "hr_documents"
    hr_docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Employee Handbook
    handbook_content = """
    EMPLOYEE HANDBOOK
    
    1. LEAVE POLICIES
    
    1.1 Vacation Leave
    All full-time employees are entitled to 20 days of paid vacation per year.
    Vacation time accrues monthly at a rate of 1.67 days per month.
    Vacation requests must be submitted at least 2 weeks in advance through the HR portal.
    Maximum vacation carryover is 5 days into the following year.
    
    1.2 Sick Leave
    Employees receive 10 days of paid sick leave annually.
    Sick leave can be used for personal illness or caring for immediate family members.
    No advance notice required for emergency situations.
    A doctor's note may be required for absences longer than 3 consecutive days.
    
    1.3 Personal Days
    All employees receive 3 personal days per year.
    Personal days must be requested 24 hours in advance when possible.
    Personal days cannot be carried over to the following year.
    
    2. ATTENDANCE POLICY
    
    2.1 Work Schedule
    Standard business hours are 9:00 AM to 5:00 PM, Monday through Friday.
    Core hours are 10:00 AM to 3:00 PM when all employees should be available.
    Flexible scheduling is available with manager approval.
    
    2.2 Remote Work
    Employees may work remotely up to 2 days per week with manager approval.
    Remote work agreements must be reviewed quarterly.
    Home office requirements must meet company safety standards.
    
    2.3 Tardiness and Absences
    Excessive tardiness (more than 3 instances per month) may result in disciplinary action.
    Unexcused absences will result in unpaid time off.
    
    3. BENEFITS
    
    3.1 Health Insurance
    Company provides comprehensive health insurance for all full-time employees.
    Coverage begins on the first day of the month following 30 days of employment.
    Company pays 80% of premium costs for employee coverage.
    Family coverage is available with employee contribution.
    
    3.2 Dental and Vision
    Dental and vision insurance is available as optional benefits.
    Premiums are deducted pre-tax from employee paychecks.
    
    3.3 Retirement Benefits
    401(k) plan available to all employees after 90 days of employment.
    Company matches 50% of employee contributions up to 6% of salary.
    Vesting schedule: 100% vested after 3 years of service.
    
    3.4 Life Insurance
    Basic life insurance coverage equal to 1x annual salary provided at no cost.
    Additional voluntary coverage available for purchase.
    
    4. PROFESSIONAL DEVELOPMENT
    
    4.1 Training and Education
    Annual professional development budget of $2,000 per employee.
    Conference attendance requires advance approval.
    Tuition reimbursement available for job-related education.
    
    4.2 Performance Reviews
    Annual performance reviews conducted each January.
    Mid-year check-ins scheduled in July.
    Performance ratings affect merit increases and promotion eligibility.
    """
    
    # IT Policies
    it_policy_content = """
    INFORMATION TECHNOLOGY POLICIES
    
    1. COMPUTER USAGE POLICY
    
    1.1 Acceptable Use
    Company computers are provided for business purposes.
    Limited personal use is permitted during break times.
    Prohibited activities include gaming, streaming, and social media during work hours.
    
    1.2 Security Requirements
    Passwords must be changed every 90 days.
    Multi-factor authentication required for all systems.
    USB devices must be approved by IT department.
    
    1.3 Software Installation
    Only pre-approved software may be installed.
    Software license compliance is mandatory.
    Personal software installation requires IT approval.
    
    2. EMAIL AND COMMUNICATION
    
    2.1 Email Usage
    Company email for business communication only.
    Personal emails should be minimal and appropriate.
    Email retention policy: 3 years for business communications.
    
    2.2 Instant Messaging
    Microsoft Teams is the approved platform for internal communication.
    External messaging platforms require approval.
    Professional communication standards apply to all platforms.
    
    3. DATA PROTECTION
    
    3.1 Confidential Information
    Employee data, customer information, and trade secrets must be protected.
    Access to confidential information based on job requirements only.
    Data sharing requires proper authorization.
    
    3.2 Backup and Recovery
    Critical data backed up daily.
    Employees responsible for organizing local files for backup inclusion.
    Disaster recovery procedures tested quarterly.
    """
    
    # Benefits Guide
    benefits_content = """
    EMPLOYEE BENEFITS GUIDE
    
    1. HEALTH AND WELLNESS
    
    1.1 Medical Insurance
    Blue Cross Blue Shield PPO Plan
    $500 individual / $1,000 family deductible
    20% coinsurance after deductible
    Out-of-pocket maximum: $3,000 individual / $6,000 family
    
    1.2 Prescription Coverage
    Generic drugs: $10 copay
    Brand name drugs: $30 copay
    Specialty drugs: 20% coinsurance
    Mail order pharmacy available for maintenance medications
    
    1.3 Wellness Program
    Annual health screening: $200 HSA credit
    Fitness center membership: 50% reimbursement up to $50/month
    Smoking cessation program: Fully covered
    
    2. TIME OFF
    
    2.1 Holiday Schedule
    10 paid holidays per year
    Floating holiday: Employee's choice
    Holiday schedule published annually in December
    
    2.2 Bereavement Leave
    5 days for immediate family members
    3 days for extended family members
    Additional unpaid leave available if needed
    
    2.3 Jury Duty
    Paid time off for jury service
    Employee must provide court documentation
    
    3. FINANCIAL BENEFITS
    
    3.1 Health Savings Account (HSA)
    Available with high-deductible health plan
    Company contributes $1,000 annually
    Triple tax advantage: deductible, growth, and withdrawals
    
    3.2 Flexible Spending Account (FSA)
    Medical FSA: up to $3,050 annual contribution
    Dependent care FSA: up to $5,000 annual contribution
    Use-it-or-lose-it rule applies
    
    3.3 Employee Stock Purchase Plan
    Purchase company stock at 15% discount
    6-month offering periods
    Maximum contribution: 15% of base salary
    """
    
    # Write the documents
    documents = {
        "employee_handbook.txt": handbook_content,
        "it_policies.txt": it_policy_content,
        "benefits_guide.txt": benefits_content
    }
    
    for filename, content in documents.items():
        file_path = hr_docs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        logger.info(f"Created: {file_path}")
    
    logger.info(f"Created {len(documents)} sample HR documents")
    return list(documents.keys())


def setup_vector_database():
    """Initialize and populate the vector database."""
    logger.info("Setting up vector database...")
    
    try:
        from tools.policy_rag.document_processor import DocumentProcessor
        from tools.policy_rag.vector_database import VectorDatabase
        
        # Initialize components
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        vector_db = VectorDatabase()
        
        # Process HR documents
        hr_docs_path = project_root / "data" / "hr_documents"
        
        if not hr_docs_path.exists():
            logger.warning("HR documents directory not found. Creating sample documents...")
            create_sample_hr_documents()
        
        # Clear existing database
        logger.info("Clearing existing database...")
        vector_db.clear_collection()
        
        # Process and add documents
        logger.info("Processing documents...")
        chunks = processor.process_directory(str(hr_docs_path))
        
        if not chunks:
            logger.error("No documents were processed!")
            return False
        
        logger.info(f"Processed {len(chunks)} chunks from HR documents")
        
        # Add to vector database
        success = vector_db.add_documents(chunks)
        
        if success:
            # Get final stats
            stats = vector_db.get_collection_stats()
            logger.info(f"Vector database setup complete: {stats}")
            return True
        else:
            logger.error("Failed to add documents to vector database")
            return False
            
    except Exception as e:
        logger.error(f"Vector database setup failed: {e}")
        return False


def test_system_components():
    """Test all system components to ensure they're working."""
    logger.info("Testing system components...")
    
    try:
        # Test MCP Server
        from mcp_server.server import MCPServer, MCPRouter
        
        server = MCPServer()
        router = MCPRouter(server)
        
        # Health check
        health = server.health_check()
        logger.info(f"MCP Server health: {health.get('server_status', 'unknown')}")
        
        # Test policy search
        result = router.route_call(
            "policy_search",
            {"query": "vacation days", "top_k": 3},
            user_id="test_user"
        )
        
        if result["success"]:
            logger.info("✓ Policy search test passed")
            search_result = result["result"]
            logger.info(f"  Found {len(search_result.get('chunks', []))} results")
        else:
            logger.error(f"✗ Policy search test failed: {result.get('error')}")
            return False
        
        # Test RAG engine
        from tools.policy_rag.rag_engine import RAGEngine
        
        rag = RAGEngine()
        if rag.client:
            logger.info("✓ RAG engine initialized with OpenAI client")
        else:
            logger.warning("⚠ RAG engine initialized without OpenAI client (API key missing)")
        
        logger.info("✓ All system components test passed")
        return True
        
    except Exception as e:
        logger.error(f"System component test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 HR Agent MCP Setup")
    print("=" * 50)
    
    # Create sample documents
    print("\n1. Creating sample HR documents...")
    try:
        documents = create_sample_hr_documents()
        print(f"✓ Created {len(documents)} sample documents")
    except Exception as e:
        print(f"✗ Failed to create sample documents: {e}")
        return
    
    # Setup vector database
    print("\n2. Setting up vector database...")
    if setup_vector_database():
        print("✓ Vector database setup complete")
    else:
        print("✗ Vector database setup failed")
        return
    
    # Test components
    print("\n3. Testing system components...")
    if test_system_components():
        print("✓ All components working correctly")
    else:
        print("✗ Component tests failed")
        return
    
    # Final instructions
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("To run the HR Assistant Agent:")
    print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the UI: streamlit run ui/streamlit_app.py")
    print("\nTo test individual components:")
    print("- Test MCP server: python mcp_server/server.py")
    print("- Test RAG engine: python tools/policy_rag/rag_engine.py")
    print("- Test vector DB: python tools/policy_rag/vector_database.py")


if __name__ == "__main__":
    main()