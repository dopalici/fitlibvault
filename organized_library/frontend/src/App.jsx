import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import TopicCard from './components/TopicCard';
import KnowledgeGraph from './components/KnowledgeGraph';
import ScanlineEffect from './components/ScanlineEffect';
import { mockApi, searchTopics, getTopicsByCategory, topicConnections } from './data/topicsData';

// Import styles
import './styles/globals.css';
import './styles/animations.css';
import './styles/terminal.css';

function App() {
  const [topics, setTopics] = useState([]);
  const [filteredTopics, setFilteredTopics] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'graph'

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [topicsResponse, categoriesResponse] = await Promise.all([
          mockApi.getTopics(),
          mockApi.getCategories()
        ]);
        
        setTopics(topicsResponse.topics);
        setFilteredTopics(topicsResponse.topics);
        setCategories(categoriesResponse);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle search
  const handleSearch = (query) => {
    setSearchQuery(query);
    
    if (!query) {
      // If no search query, show category filter or all topics
      if (selectedCategory) {
        setFilteredTopics(getTopicsByCategory(selectedCategory, topics));
      } else {
        setFilteredTopics(topics);
      }
    } else {
      // Search within current topic set
      const baseTopics = selectedCategory 
        ? getTopicsByCategory(selectedCategory, topics) 
        : topics;
      setFilteredTopics(searchTopics(query, baseTopics));
    }
  };

  // Handle category selection
  const handleCategorySelect = (categoryId) => {
    if (selectedCategory === categoryId) {
      // Deselect category
      setSelectedCategory(null);
      setFilteredTopics(searchQuery ? searchTopics(searchQuery, topics) : topics);
    } else {
      // Select new category
      setSelectedCategory(categoryId);
      const categoryTopics = getTopicsByCategory(categoryId, topics);
      setFilteredTopics(searchQuery ? searchTopics(searchQuery, categoryTopics) : categoryTopics);
    }
  };

  // Handle topic selection
  const handleTopicSelect = (topicId) => {
    setSelectedTopic(topicId);
    // In a real app, this would navigate to the topic detail page
    console.log('Selected topic:', topicId);
  };

  // Toggle menu
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  // Get current view title
  const getViewTitle = () => {
    if (searchQuery) {
      return `Search Results: "${searchQuery}"`;
    }
    if (selectedCategory) {
      const category = categories.find(c => c.id === selectedCategory);
      return category ? category.name : 'Unknown Category';
    }
    return 'All Topics';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="terminal-window">
          <div className="terminal-content text-center">
            <div className="loading-dots mb-md">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div className="text-glow">INITIALIZING NEURAL NETWORK...</div>
            <div className="text-sm text-muted mt-sm">Loading fitness database</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-primary text-primary">
      {/* CRT Scanline Effect */}
      <ScanlineEffect />
      
      {/* Main Layout */}
      <div className="container py-md">
        {/* Header */}
        <Header 
          onSearch={handleSearch}
          onMenuToggle={toggleMenu}
          isMenuOpen={isMenuOpen}
        />

        {/* Main Content Area */}
        <div className="grid grid-cols-12 gap-lg">
          {/* Navigation Sidebar */}
          {isMenuOpen && (
            <div className="col-span-12 lg:col-span-3">
              <Navigation 
                isOpen={isMenuOpen}
                onCategorySelect={handleCategorySelect}
                selectedCategory={selectedCategory}
              />
            </div>
          )}

          {/* Content Area */}
          <div className={`col-span-12 ${isMenuOpen ? 'lg:col-span-9' : ''}`}>
            {/* View Controls */}
            <div className="flex items-center justify-between mb-lg">
              <div>
                <h2 className="text-xl text-glow mb-xs">{getViewTitle()}</h2>
                <div className="text-sm text-muted">
                  {filteredTopics.length} topics • {topics.length} total in database
                </div>
              </div>
              
              <div className="flex gap-xs">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`btn ${viewMode === 'grid' ? 'btn-primary' : ''}`}
                >
                  GRID
                </button>
                <button
                  onClick={() => setViewMode('graph')}
                  className={`btn ${viewMode === 'graph' ? 'btn-primary' : ''}`}
                >
                  GRAPH
                </button>
              </div>
            </div>

            {/* Content Display */}
            {viewMode === 'graph' ? (
              // Knowledge Graph View
              <KnowledgeGraph
                topics={filteredTopics}
                connections={topicConnections}
                selectedTopic={selectedTopic}
                onTopicSelect={handleTopicSelect}
              />
            ) : (
              // Grid View
              <>
                {filteredTopics.length === 0 ? (
                  <div className="terminal-window text-center">
                    <div className="terminal-content">
                      <div className="text-glow mb-md">NO RESULTS FOUND</div>
                      <div className="terminal-output">
                        <div className="terminal-line error">
                          <span className="terminal-line-prefix">!</span>
                          <span className="terminal-line-content">
                            No topics match your current filters
                          </span>
                        </div>
                        <div className="terminal-line">
                          <span className="terminal-line-prefix">$</span>
                          <span className="terminal-line-content">
                            Try adjusting your search query or category selection
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-3 gap-lg">
                    {filteredTopics.map((topic, index) => (
                      <div 
                        key={topic.id} 
                        style={{ animationDelay: `${index * 0.1}s` }}
                      >
                        <TopicCard
                          topic={topic}
                          onTopicClick={handleTopicSelect}
                          showConnections={true}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Terminal Status Bar */}
      <div className="terminal-status">
        <div className="status-left">
          <div className="status-item">
            <div className="status-indicator connected"></div>
            <span>SYSTEM ONLINE</span>
          </div>
          <div className="status-item">
            <span>FITNESS_LIBRARY v2.0.1</span>
          </div>
          <div className="status-item">
            <span>TOPICS: {topics.length}</span>
          </div>
        </div>
        
        <div className="status-right">
          <div className="status-item">
            <span>VIEW: {viewMode.toUpperCase()}</span>
          </div>
          <div className="status-item">
            <span>FILTER: {selectedCategory || 'ALL'}</span>
          </div>
          <div className="status-item">
            <div className="status-indicator"></div>
            <span>READY</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;