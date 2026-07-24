from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String) # Admin, Recruiter, HR, HiringManager, Candidate
    created_at = Column(DateTime, default=datetime.utcnow)

class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    jobs = relationship("Job", back_populates="company")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"))
    title = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    location = Column(String)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="jobs")
    candidates = relationship("CandidateProfile", back_populates="job")

class CandidateProfile(Base):
    __tablename__ = "candidates"
    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    name = Column(String)
    email = Column(String)
    skills = Column(String) # Comma separated
    experience_years = Column(Float, default=0.0)
    education = Column(String)
    location = Column(String)
    availability = Column(String)
    expected_salary = Column(String)
    
    # Ranking metrics
    ats_score = Column(Float, default=0.0)
    interview_score = Column(Float, default=0.0)
    portfolio_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    hiring_recommendation = Column(String)
    
    is_shortlisted = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="candidates")
    comments = relationship("Comment", back_populates="candidate")

class InterviewRecord(Base):
    __tablename__ = "interviews"
    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"))
    role = Column(String)
    questions = Column(JSON) # List of questions
    difficulty = Column(String)
    prep_tips = Column(Text)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"))
    user_id = Column(String, ForeignKey("users.id"))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    candidate = relationship("CandidateProfile", back_populates="comments")
    user = relationship("User")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Phase E Models (AI Career Ecosystem) ---

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    theme = Column(String, default="modern")
    projects = Column(JSON)
    certifications = Column(JSON)
    skills = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class GitHubProfile(Base):
    __tablename__ = "github_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    username = Column(String)
    commit_activity = Column(Integer, default=0)
    code_quality_score = Column(Float, default=0.0)
    top_languages = Column(JSON)
    repository_score = Column(Float, default=0.0)
    recommendations = Column(JSON)

class LinkedInProfile(Base):
    __tablename__ = "linkedin_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    profile_url = Column(String)
    strength_score = Column(Float, default=0.0)
    visibility_score = Column(Float, default=0.0)
    suggestions = Column(JSON)

class Mentor(Base):
    __tablename__ = "mentors"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    expertise = Column(String)
    rating = Column(Float, default=5.0)
    hourly_rate = Column(Float, default=0.0)
    bio = Column(Text)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=generate_uuid)
    mentor_id = Column(String, ForeignKey("mentors.id"))
    mentee_id = Column(String, ForeignKey("users.id"))
    scheduled_at = Column(DateTime)
    status = Column(String, default="Scheduled")
    notes = Column(Text)

class CommunityPost(Base):
    __tablename__ = "community_posts"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    category = Column(String) # Discussion, Q&A, Peer Review
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)

class JobAlert(Base):
    __tablename__ = "job_alerts"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    keywords = Column(String)
    location = Column(String)
    frequency = Column(String, default="Daily")

class LearningGoal(Base):
    __tablename__ = "learning_goals"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    skill = Column(String)
    progress_percentage = Column(Integer, default=0)
    deadline = Column(DateTime)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    message = Column(Text)
    type = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Phase F Models (Global AI Career Cloud) ---

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    provider = Column(String) # Google, GitHub, Microsoft
    provider_account_id = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class CloudStorageFile(Base):
    __tablename__ = "cloud_files"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    filename = Column(String)
    provider = Column(String) # S3, Azure, Local
    url = Column(String)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class GitHubAccount(Base):
    __tablename__ = "github_accounts"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    username = Column(String)
    total_commits = Column(Integer, default=0)
    top_languages = Column(String)
    developer_score = Column(Float, default=0.0)
    last_synced = Column(DateTime, default=datetime.utcnow)

class JobApplication(Base):
    __tablename__ = "job_applications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    company_name = Column(String)
    job_title = Column(String)
    status = Column(String, default="Applied")
    source = Column(String) # Indeed, LinkedIn, Direct
    applied_at = Column(DateTime, default=datetime.utcnow)

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    meeting_link = Column(String)

class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    subject = Column(String)
    status = Column(String, default="Sent")
    sent_at = Column(DateTime, default=datetime.utcnow)

class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    url = Column(String)
    event_type = Column(String)
    is_active = Column(Boolean, default=True)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutomationTask(Base):
    __tablename__ = "automation_tasks"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    task_name = Column(String)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    metric_name = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

# --- Phase G Models (AI Talent Intelligence Platform) ---

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    industry = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TalentGraphNode(Base):
    __tablename__ = "talent_nodes"
    id = Column(String, primary_key=True, default=generate_uuid)
    node_type = Column(String) # Candidate, Skill, Company
    name = Column(String)
    metadata_json = Column(String)

class TalentGraphEdge(Base):
    __tablename__ = "talent_edges"
    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, ForeignKey("talent_nodes.id"))
    target_id = Column(String, ForeignKey("talent_nodes.id"))
    relationship = Column(String) # WORKED_AT, HAS_SKILL
    weight = Column(Float, default=1.0)

class CandidateRanking(Base):
    __tablename__ = "candidate_rankings"
    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("users.id"))
    job_role = Column(String)
    match_score = Column(Float)
    confidence_score = Column(Float)
    ranked_at = Column(DateTime, default=datetime.utcnow)

class SalaryBenchmark(Base):
    __tablename__ = "salary_benchmarks"
    id = Column(String, primary_key=True, default=generate_uuid)
    role = Column(String)
    location = Column(String)
    average_salary = Column(Integer)
    min_salary = Column(Integer)
    max_salary = Column(Integer)
    currency = Column(String, default="USD")

class WorkforcePlan(Base):
    __tablename__ = "workforce_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"))
    department = Column(String)
    forecasted_hires = Column(Integer)
    target_quarter = Column(String) # e.g., "Q3 2026"
    budget = Column(Integer)

# --- Phase H Models (AI Learning Platform) ---

class Course(Base):
    __tablename__ = "courses"
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    description = Column(Text)
    difficulty = Column(String) # Beginner, Intermediate, Advanced
    category = Column(String)
    estimated_hours = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Module(Base):
    __tablename__ = "modules"
    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"))
    title = Column(String)
    order_index = Column(Integer)

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(String, primary_key=True, default=generate_uuid)
    module_id = Column(String, ForeignKey("modules.id"))
    title = Column(String)
    content_type = Column(String) # Video, Text, CodeLab
    content_url = Column(String)
    order_index = Column(Integer)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    progress_percentage = Column(Integer, default=0)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(String, primary_key=True, default=generate_uuid)
    module_id = Column(String, ForeignKey("modules.id"))
    title = Column(String)
    total_score = Column(Integer)

class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    question_text = Column(Text)
    question_type = Column(String) # MCQ, Coding
    options_json = Column(String) # Serialized list if MCQ
    correct_answer = Column(String)

class Answer(Base):
    __tablename__ = "answers"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    provided_answer = Column(String)
    is_correct = Column(Boolean)

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    issue_date = Column(DateTime, default=datetime.utcnow)
    verification_id = Column(String, unique=True, default=generate_uuid)

class Badge(Base):
    __tablename__ = "badges"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    badge_name = Column(String)
    icon_url = Column(String)
    earned_at = Column(DateTime, default=datetime.utcnow)

class StudyGroup(Base):
    __tablename__ = "study_groups"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    description = Column(String)
    created_by = Column(String, ForeignKey("users.id"))

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("study_groups.id"))
    user_id = Column(String, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(String, primary_key=True, default=generate_uuid)
    lesson_id = Column(String, ForeignKey("lessons.id"))
    title = Column(String)
    description = Column(Text)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True, default=generate_uuid)
    assignment_id = Column(String, ForeignKey("assignments.id"))
    user_id = Column(String, ForeignKey("users.id"))
    code_content = Column(Text)
    score = Column(Float, nullable=True)

class Leaderboard(Base):
    __tablename__ = "leaderboards"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    total_xp = Column(Integer, default=0)
    current_level = Column(Integer, default=1)
    streak_days = Column(Integer, default=0)

class Progress(Base):
    __tablename__ = "progress_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    lesson_id = Column(String, ForeignKey("lessons.id"))
    completed_at = Column(DateTime, default=datetime.utcnow)

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(String, primary_key=True, default=generate_uuid)
    course_id = Column(String, ForeignKey("courses.id"))
    front = Column(String)
    back = Column(Text)

class LearningSession(Base):
    __tablename__ = "learning_sessions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    duration_minutes = Column(Integer)
    session_date = Column(DateTime, default=datetime.utcnow)

# --- Phase I Models (AI Marketplace) ---

class SellerProfile(Base):
    __tablename__ = "seller_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    bio = Column(Text)
    skills = Column(String)
    hourly_rate = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    earnings = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BuyerProfile(Base):
    __tablename__ = "buyer_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    company_name = Column(String)
    industry = Column(String)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class GigCategory(Base):
    __tablename__ = "gig_categories"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True)
    description = Column(Text)

class Gig(Base):
    __tablename__ = "gigs"
    id = Column(String, primary_key=True, default=generate_uuid)
    seller_id = Column(String, ForeignKey("seller_profiles.id"))
    category_id = Column(String, ForeignKey("gig_categories.id"))
    title = Column(String)
    description = Column(Text)
    price = Column(Float)
    delivery_days = Column(Integer)
    revisions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=generate_uuid)
    buyer_id = Column(String, ForeignKey("buyer_profiles.id"))
    title = Column(String)
    description = Column(Text)
    budget = Column(Float)
    deadline = Column(DateTime)
    skills_required = Column(String)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String)
    amount = Column(Float)
    status = Column(String, default="Pending")
    due_date = Column(DateTime)

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"))
    seller_id = Column(String, ForeignKey("seller_profiles.id"))
    cover_letter = Column(Text)
    bid_amount = Column(Float)
    estimated_days = Column(Integer)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    buyer_id = Column(String, ForeignKey("users.id"))
    seller_id = Column(String, ForeignKey("users.id"))
    gig_id = Column(String, ForeignKey("gigs.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    amount = Column(Float)
    status = Column(String, default="Pending")
    delivery_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    reviewer_id = Column(String, ForeignKey("users.id"))
    reviewee_id = Column(String, ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True, default=generate_uuid)
    wallet_id = Column(String, ForeignKey("wallets.id"))
    amount = Column(Float)
    type = Column(String) # Credit, Debit
    status = Column(String, default="Completed")
    reference = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    raised_by = Column(String, ForeignKey("users.id"))
    reason = Column(Text)
    status = Column(String, default="Open")
    created_at = Column(DateTime, default=datetime.utcnow)

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True)
    discount_percentage = Column(Float)
    max_discount = Column(Float)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

class MarketplaceAnalytics(Base):
    __tablename__ = "marketplace_analytics"
    id = Column(String, primary_key=True, default=generate_uuid)
    metric_name = Column(String)
    metric_value = Column(Float)
    dimension = Column(String)
    recorded_at = Column(DateTime, default=datetime.utcnow)

# --- Phase J Models (Global Talent Network) ---

class Profile(Base):
    __tablename__ = "network_profiles"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    headline = Column(String)
    about = Column(Text)
    avatar_url = Column(String)
    location = Column(String)
    website = Column(String)

class Connection(Base):
    __tablename__ = "connections"
    id = Column(String, primary_key=True, default=generate_uuid)
    requester_id = Column(String, ForeignKey("users.id"))
    recipient_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="Pending") # Pending, Accepted, Blocked
    created_at = Column(DateTime, default=datetime.utcnow)

class Follow(Base):
    __tablename__ = "follows"
    id = Column(String, primary_key=True, default=generate_uuid)
    follower_id = Column(String, ForeignKey("users.id"))
    following_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True, default=generate_uuid)
    author_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    media_url = Column(String, nullable=True)
    post_type = Column(String, default="Update") # Achievement, Learning, Showcase, Announcement
    created_at = Column(DateTime, default=datetime.utcnow)

class Comment(Base):
    __tablename__ = "post_comments"
    id = Column(String, primary_key=True, default=generate_uuid)
    post_id = Column(String, ForeignKey("posts.id"))
    author_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Reaction(Base):
    __tablename__ = "post_reactions"
    id = Column(String, primary_key=True, default=generate_uuid)
    post_id = Column(String, ForeignKey("posts.id"))
    user_id = Column(String, ForeignKey("users.id"))
    reaction_type = Column(String) # Like, Celebrate, Insightful
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_type = Column(String, default="Direct") # Direct, Group
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Community(Base):
    __tablename__ = "communities"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    description = Column(Text)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityMember(Base):
    __tablename__ = "community_members"
    id = Column(String, primary_key=True, default=generate_uuid)
    community_id = Column(String, ForeignKey("communities.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, default="Member") # Admin, Member
    joined_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String)
    description = Column(Text)
    event_type = Column(String) # Virtual, Hackathon, Meetup
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    organizer_id = Column(String, ForeignKey("users.id"))

class EventRegistration(Base):
    __tablename__ = "event_registrations"
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("events.id"))
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default="Registered") # Registered, Attended
    registered_at = Column(DateTime, default=datetime.utcnow)

class NetworkReputation(Base):
    __tablename__ = "network_reputation"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    influence_score = Column(Float, default=0.0)
    contribution_score = Column(Float, default=0.0)
    badges = Column(String) # JSON string array

# --- Phase K Models (AI Career Copilot) ---

class CareerGoal(Base):
    __tablename__ = "career_goals"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text)
    target_date = Column(DateTime)
    status = Column(String, default="In Progress")
    created_at = Column(DateTime, default=datetime.utcnow)

class CareerPlan(Base):
    __tablename__ = "career_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, ForeignKey("career_goals.id"))
    plan_content = Column(Text) # AI generated plan steps (JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    goal_id = Column(String, ForeignKey("career_goals.id"), nullable=True)
    title = Column(String)
    is_completed = Column(Boolean, default=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class JobRecommendation(Base):
    __tablename__ = "job_recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    job_title = Column(String)
    company = Column(String)
    match_score = Column(Float)
    status = Column(String, default="Suggested") # Suggested, Applied, Rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class SalaryInsight(Base):
    __tablename__ = "salary_insights"
    id = Column(String, primary_key=True, default=generate_uuid)
    job_title = Column(String)
    location = Column(String)
    min_salary = Column(Float)
    max_salary = Column(Float)
    median_salary = Column(Float)
    currency = Column(String, default="USD")
    last_updated = Column(DateTime, default=datetime.utcnow)

class VoiceSession(Base):
    __tablename__ = "voice_sessions"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    transcript = Column(Text)
    intent_detected = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    trigger_event = Column(String) # e.g., "Weekly", "On Profile View"
    action_type = Column(String) # e.g., "Send Report", "Draft Message"
    is_active = Column(Boolean, default=True)

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    remind_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)

class CareerMetric(Base):
    __tablename__ = "career_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    metric_type = Column(String) # "Interviews", "Applications"
    value = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    agent_type = Column(String) # "Coordinator", "ResumeAgent", "SalaryAgent"
    query = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentMemory(Base):
    __tablename__ = "agent_memories"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    context_key = Column(String)
    context_value = Column(Text) # JSON string
    updated_at = Column(DateTime, default=datetime.utcnow)

class Planner(Base):
    __tablename__ = "planners"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    planner_type = Column(String) # "Daily", "Weekly"
    content = Column(Text)
    date = Column(DateTime)

class GoalProgress(Base):
    __tablename__ = "goal_progress"
    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, ForeignKey("career_goals.id"))
    progress_percentage = Column(Float, default=0.0)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CareerReport(Base):
    __tablename__ = "career_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    report_type = Column(String) # "Weekly", "Monthly"
    summary = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

# --- Phase L Models (Enterprise SaaS Platform) ---

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

class TenantSettings(Base):
    __tablename__ = "tenant_settings"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), unique=True)
    sso_provider = Column(String, nullable=True) # "SAML", "OIDC", "AzureAD"
    sso_config = Column(Text, nullable=True) # JSON payload
    data_retention_days = Column(Integer, default=365)

class TenantMembership(Base):
    """Junction table linking global Users to SaaS Tenants without altering the User table."""
    __tablename__ = "tenant_memberships"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role_id = Column(String, ForeignKey("roles.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

class OrganizationBranding(Base):
    __tablename__ = "organization_branding"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), unique=True)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, default="#0d9488")
    custom_css = Column(Text, nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    plan_name = Column(String) # "Enterprise", "Pro"
    status = Column(String, default="Active")
    current_period_end = Column(DateTime)
    ai_credits_limit = Column(Integer, default=1000)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(String, default="Paid")
    issued_at = Column(DateTime, default=datetime.utcnow)

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    metric_name = Column(String) # e.g., "AI_Parse", "API_Call"
    quantity = Column(Integer, default=1)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True) # Null for global roles
    name = Column(String) # "Super Admin", "HR Admin", "Hiring Manager"

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True) # "manage_users", "view_billing"

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(String, primary_key=True, default=generate_uuid)
    role_id = Column(String, ForeignKey("roles.id"))
    permission_id = Column(String, ForeignKey("permissions.id"))

class ApiCredential(Base):
    __tablename__ = "api_credentials"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    api_key_hash = Column(String)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    url = Column(String)
    secret = Column(String)
    events = Column(String) # JSON array

class Department(Base):
    __tablename__ = "departments"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    name = Column(String)

class UserDepartment(Base):
    __tablename__ = "user_departments"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    department_id = Column(String, ForeignKey("departments.id"))

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    resource = Column(String)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    policy_name = Column(String) # e.g., "GDPR_Data_Deletion"
    status = Column(String)
    checked_at = Column(DateTime, default=datetime.utcnow)

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    metric_type = Column(String) # "CPU", "Memory", "API_Latency"
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class BackupRecord(Base):
    __tablename__ = "backup_records"
    id = Column(String, primary_key=True, default=generate_uuid)
    backup_type = Column(String) # "Full", "Incremental"
    s3_path = Column(String)
    status = Column(String)
    completed_at = Column(DateTime)

# --- Phase M Models (AI Operating System Platform) ---

class Plugin(Base):
    __tablename__ = "plugins"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True)
    developer = Column(String)
    version = Column(String)
    description = Column(Text)
    manifest = Column(Text) # JSON schema for plugin config

class PluginInstallation(Base):
    __tablename__ = "plugin_installations"
    id = Column(String, primary_key=True, default=generate_uuid)
    plugin_id = Column(String, ForeignKey("plugins.id"))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True) # Global if null
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="Active")
    config = Column(Text) # JSON configuration

class PluginPermission(Base):
    __tablename__ = "plugin_permissions"
    id = Column(String, primary_key=True, default=generate_uuid)
    plugin_id = Column(String, ForeignKey("plugins.id"))
    resource_scope = Column(String) # e.g., "read:resume", "write:goals"

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    definition = Column(Text) # JSON DAG definition
    is_active = Column(Boolean, default=True)

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"))
    status = Column(String) # "Running", "Completed", "Failed"
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    capabilities = Column(String) # JSON array of skills
    description = Column(Text)

class AgentTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=True)
    payload = Column(Text)
    status = Column(String) # "Pending", "Running", "Requires_Approval"

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("agent_tasks.id"))
    result = Column(Text)
    execution_time_ms = Column(Integer)

class Function(Base):
    __tablename__ = "functions"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    code = Column(Text) # User script
    runtime = Column(String) # "python3.10", "nodejs18"

class FunctionExecution(Base):
    __tablename__ = "function_executions"
    id = Column(String, primary_key=True, default=generate_uuid)
    function_id = Column(String, ForeignKey("functions.id"))
    status = Column(String)
    logs = Column(Text)

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(String, primary_key=True, default=generate_uuid)
    model_name = Column(String)
    version = Column(String)
    is_active = Column(Boolean, default=True)

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("model_registry.id"))
    name = Column(String)
    template_text = Column(Text)
    ab_test_group = Column(String, nullable=True)

class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    url = Column(String)
    events = Column(String)

class ApiUsage(Base):
    __tablename__ = "api_usage"
    id = Column(String, primary_key=True, default=generate_uuid)
    api_key_id = Column(String, ForeignKey("api_credentials.id"))
    endpoint = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PlatformMetric(Base):
    __tablename__ = "platform_metrics"
    id = Column(String, primary_key=True, default=generate_uuid)
    metric = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    id = Column(String, primary_key=True, default=generate_uuid)
    flag_name = Column(String, unique=True)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String, unique=True)
    value = Column(Text)
