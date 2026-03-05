-- 01_create_tables.sql
-- Production-ready schema for Kipaji Chetu

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

-- Indexes for performance
CREATE INDEX idx_quiz_attempts_student ON quiz_attempts(student_id);
CREATE INDEX idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX idx_performance_logs_student ON performance_logs(student_id);
CREATE INDEX idx_ai_feedback_student ON ai_feedback_logs(student_id);