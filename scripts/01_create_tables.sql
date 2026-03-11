-- 01_create_tables.sql
-- Production-ready schema for Kipaji Chetu
-- run in
-- Students table: stores learner profile & adaptive settings
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    
    learning_mode VARCHAR(50) DEFAULT 'normal',   -- 'normal' or 'simplified'
    accessibility_enabled BOOLEAN DEFAULT FALSE,  -- TTS flag
    
    risk_score FLOAT DEFAULT 0.0,                  -- predictive at-risk indicator
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topics table: organizes learning subjects
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    difficulty_level VARCHAR(50) DEFAULT 'medium',  -- overall topic difficulty
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quizzes table: stores AI-generated or static questions
CREATE TABLE IF NOT EXISTS quizzes (
    id SERIAL PRIMARY KEY,
    topic_id INT REFERENCES topics(id) ON DELETE CASCADE,
    
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    
    correct_answer VARCHAR(1) NOT NULL CHECK (correct_answer IN ('A','B','C','D')),
    difficulty_level VARCHAR(50),                    -- per-question difficulty
    
    ai_generated BOOLEAN DEFAULT TRUE,               -- track AI usage
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quiz attempts table: most important for analytics
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    quiz_id INT REFERENCES quizzes(id) ON DELETE CASCADE,
    
    selected_answer VARCHAR(1) CHECK (selected_answer IN ('A','B','C','D')),
    is_correct BOOLEAN,
    score FLOAT CHECK (score >= 0 AND score <= 100),
    
    time_taken INT,                                   -- seconds spent
    attempt_number INT DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance logs: precomputed metrics per student/topic
CREATE TABLE IF NOT EXISTS performance_logs (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    topic_id INT REFERENCES topics(id) ON DELETE CASCADE,
    
    average_score FLOAT,
    improvement_rate FLOAT,                           -- trend slope
    mastery_level FLOAT,                               -- e.g., 0-100
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, topic_id)                       -- one row per pair
);

-- AI feedback logs: governance & traceability
CREATE TABLE IF NOT EXISTS ai_feedback_logs (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    quiz_id INT REFERENCES quizzes(id),
    
    prompt TEXT,                                       -- what was sent to OpenAI
    ai_response TEXT,                                  -- generated feedback
    simplified_mode BOOLEAN DEFAULT FALSE,             -- was simplified?
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teacher notes: bonus feature for educators
CREATE TABLE IF NOT EXISTS teacher_notes (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(id) ON DELETE CASCADE,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- advance with new ew tables for teacher & class management
-- =====================================================

-- Teachers (can be extended with authentication later)
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255),          -- for future login
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classes created by teachers
CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    class_code VARCHAR(20) UNIQUE NOT NULL,   -- e.g., "MATH101"
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    subject VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship between students and classes
CREATE TABLE IF NOT EXISTS class_students (
    id SERIAL PRIMARY KEY,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, student_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_performance_logs_student ON performance_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_student ON ai_feedback_logs(student_id);


