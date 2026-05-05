-- ================================================
-- FitLib Knowledge Base - PostgreSQL Database Schema
-- Version: 1.0
-- Purpose: Web app backend for interactive fitness library
-- ================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For multi-column indexes

-- ================================================
-- CORE CONTENT TABLES
-- ================================================

-- Main content nodes (fitness topics)
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) UNIQUE NOT NULL,  -- e.g., "A1-ENERGY-BALANCE"
    title VARCHAR(500) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    series VARCHAR(100) NOT NULL,  -- foundational, resistance_training, nutrition, etc.
    
    -- Content sections (stored as JSONB for flexibility)
    content_sections JSONB NOT NULL,
    full_markdown TEXT NOT NULL,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    credibility_score DECIMAL(3,2) DEFAULT 0.50,
    citation_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    link_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_date VARCHAR(50),
    updated_date VARCHAR(50),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(content_sections->>'quick_takeaway', '')), 'B') ||
        setweight(to_tsvector('english', coalesce(content_sections->>'key_points', '')), 'C') ||
        setweight(to_tsvector('english', coalesce(full_markdown, '')), 'D')
    ) STORED
);

-- Internal links between nodes
CREATE TABLE node_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    link_text VARCHAR(500),
    link_position INTEGER,  -- Position in source markdown
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_node_id, target_node_id, link_text)
);

-- Citations/Research papers
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    
    authors TEXT NOT NULL,
    title TEXT NOT NULL,
    journal VARCHAR(500),
    doi VARCHAR(255),
    
    -- Quality indicators
    quality_rating VARCHAR(50),  -- High, Medium, Low
    study_type VARCHAR(100),     -- Meta-analysis, RCT, Review, etc.
    automation_validated BOOLEAN DEFAULT true,
    
    -- Credibility metrics (from your automation tools)
    impact_factor DECIMAL(5,2),
    bias_score DECIMAL(3,2),
    grade_assessment VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- USER MANAGEMENT TABLES
-- ================================================

-- User accounts
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed
    
    -- Profile
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    bio TEXT,
    
    -- Account status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User favorites/bookmarks
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    
    -- Reading progress
    read_position INTEGER DEFAULT 0,  -- Percentage
    is_completed BOOLEAN DEFAULT false,
    last_read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Personal notes
    personal_notes TEXT,
    tags TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, node_id)
);

-- User reading history
CREATE TABLE reading_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    
    -- Session tracking
    session_duration INTEGER,  -- seconds
    read_percentage INTEGER,
    device_type VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User progress dashboard
CREATE TABLE user_progress (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Overall stats
    total_nodes_read INTEGER DEFAULT 0,
    total_time_minutes INTEGER DEFAULT 0,
    study_streak_days INTEGER DEFAULT 0,
    last_study_date DATE,
    
    -- Series completion
    foundational_completion DECIMAL(5,2) DEFAULT 0,
    resistance_training_completion DECIMAL(5,2) DEFAULT 0,
    nutrition_completion DECIMAL(5,2) DEFAULT 0,
    cardiovascular_completion DECIMAL(5,2) DEFAULT 0,
    
    -- Gamification
    achievement_points INTEGER DEFAULT 0,
    badges TEXT[] DEFAULT '{}',
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- ANALYTICS & ENGAGEMENT
-- ================================================

-- Node popularity metrics
CREATE TABLE node_analytics (
    node_id UUID PRIMARY KEY REFERENCES nodes(id) ON DELETE CASCADE,
    
    -- Engagement metrics
    total_views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    total_favorites INTEGER DEFAULT 0,
    average_read_time INTEGER DEFAULT 0,  -- seconds
    completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Social metrics
    share_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity log
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    activity_type VARCHAR(50) NOT NULL,  -- view, favorite, note, search, etc.
    target_node_id UUID REFERENCES nodes(id) ON DELETE SET NULL,
    metadata JSONB,  -- Flexible data storage
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- SEARCH & DISCOVERY
-- ================================================

-- Saved searches
CREATE TABLE saved_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    search_query VARCHAR(500) NOT NULL,
    filters JSONB,  -- {series: [...], tags: [...], credibility: [0.8, 1.0]}
    result_count INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- INDEXES FOR PERFORMANCE
-- ================================================

-- Full-text search index
CREATE INDEX idx_nodes_search_vector ON nodes USING GIN(search_vector);

-- Fuzzy search support
CREATE INDEX idx_nodes_title_trgm ON nodes USING GIN(title gin_trgm_ops);

-- Common queries
CREATE INDEX idx_nodes_series ON nodes(series);
CREATE INDEX idx_nodes_credibility ON nodes(credibility_score DESC);
CREATE INDEX idx_nodes_tags ON nodes USING GIN(tags);
CREATE INDEX idx_citations_node ON citations(node_id);
CREATE INDEX idx_node_links_source ON node_links(source_node_id);
CREATE INDEX idx_node_links_target ON node_links(target_node_id);

-- User data queries
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_node ON user_favorites(node_id);
CREATE INDEX idx_reading_history_user ON reading_history(user_id);
CREATE INDEX idx_reading_history_created ON reading_history(created_at DESC);
CREATE INDEX idx_activity_log_user ON activity_log(user_id);
CREATE INDEX idx_activity_log_created ON activity_log(created_at DESC);

-- ================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================

-- Popular nodes
CREATE VIEW popular_nodes AS
SELECT 
    n.id,
    n.node_id,
    n.title,
    n.series,
    n.credibility_score,
    n.citation_count,
    a.total_views,
    a.total_favorites,
    a.average_read_time
FROM nodes n
LEFT JOIN node_analytics a ON n.id = a.node_id
ORDER BY a.total_views DESC;

-- User dashboard summary
CREATE VIEW user_dashboard AS
SELECT 
    u.id AS user_id,
    u.username,
    u.display_name,
    up.total_nodes_read,
    up.study_streak_days,
    COUNT(DISTINCT uf.node_id) AS favorites_count,
    MAX(rh.created_at) AS last_read_at
FROM users u
LEFT JOIN user_progress up ON u.id = up.user_id
LEFT JOIN user_favorites uf ON u.id = uf.user_id
LEFT JOIN reading_history rh ON u.id = rh.user_id
GROUP BY u.id, u.username, u.display_name, up.total_nodes_read, up.study_streak_days;

-- ================================================
-- SAMPLE QUERIES FOR API ENDPOINTS
-- ================================================

-- Full-text search with filters
COMMENT ON TABLE nodes IS '
Example search query:
SELECT id, title, series, credibility_score,
       ts_rank(search_vector, query) AS rank
FROM nodes, plainto_tsquery(''resistance training'') query
WHERE search_vector @@ query
  AND series = ''resistance_training''
  AND credibility_score >= 0.8
ORDER BY rank DESC
LIMIT 20;
';

-- Knowledge graph neighbors
COMMENT ON TABLE node_links IS '
Example graph query:
WITH RECURSIVE graph_path AS (
    SELECT source_node_id, target_node_id, 1 AS depth
    FROM node_links
    WHERE source_node_id = ''<node_uuid>''
    
    UNION
    
    SELECT nl.source_node_id, nl.target_node_id, gp.depth + 1
    FROM node_links nl
    JOIN graph_path gp ON nl.source_node_id = gp.target_node_id
    WHERE depth < 3
)
SELECT DISTINCT n.* 
FROM graph_path gp
JOIN nodes n ON n.id = gp.target_node_id;
';

-- ================================================
-- FUNCTIONS FOR AUTOMATION
-- ================================================

-- Update node analytics
CREATE OR REPLACE FUNCTION update_node_analytics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE node_analytics
        SET total_views = total_views + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE node_id = NEW.node_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_node_analytics
AFTER INSERT ON reading_history
FOR EACH ROW EXECUTE FUNCTION update_node_analytics();

-- Update user progress
CREATE OR REPLACE FUNCTION update_user_progress()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.is_completed THEN
        UPDATE user_progress
        SET total_nodes_read = total_nodes_read + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_progress
AFTER UPDATE ON user_favorites
FOR EACH ROW EXECUTE FUNCTION update_user_progress();

-- ================================================
-- SAMPLE DATA (for development)
-- ================================================

-- This will be populated from fitlib_export.json
-- Use the provided import script to load data

COMMENT ON SCHEMA public IS 'FitLib Knowledge Base Schema v1.0';
