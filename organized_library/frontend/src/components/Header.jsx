import React, { useState, useEffect } from 'react';
import { Search, Menu, X, Zap, Database, Users } from 'lucide-react';

const Header = ({ onSearch, onMenuToggle, isMenuOpen }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch(query);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <header className="terminal-window mb-lg">
      <div className="terminal-header">
        <div className="terminal-buttons">
          <div className="terminal-button close"></div>
          <div className="terminal-button minimize"></div>
          <div className="terminal-button maximize"></div>
        </div>
        <div className="terminal-title">FITNESS LIBRARY v2.0.1</div>
      </div>
      
      <div className="terminal-content">
        {/* System Status */}
        <div className="flex justify-between items-center mb-md">
          <div className="flex items-center gap-md">
            <div className="flex items-center gap-sm">
              <Zap size={16} className="text-glow" />
              <span className="text-sm text-secondary">SYSTEM ONLINE</span>
            </div>
            <div className="flex items-center gap-sm">
              <Database size={16} className="text-muted" />
              <span className="text-sm text-muted">574 TOPICS LOADED</span>
            </div>
            <div className="flex items-center gap-sm">
              <Users size={16} className="text-muted" />
              <span className="text-sm text-muted">MULTI-USER READY</span>
            </div>
          </div>
          
          <div className="text-sm text-muted">
            {formatTime(currentTime)} UTC
          </div>
        </div>

        {/* Main Header Content */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-lg">
            <button
              onClick={onMenuToggle}
              className="btn p-sm hover-glow"
              aria-label="Toggle navigation menu"
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            
            <div>
              <h1 className="text-2xl m-0 glow-pulse">
                FITNESS LIBRARY
              </h1>
              <p className="text-sm text-muted m-0">
                COMPREHENSIVE EXERCISE SCIENCE DATABASE
              </p>
            </div>
          </div>

          {/* Search Interface */}
          <div className="flex items-center gap-md">
            <div 
              className={`terminal-window ${isSearchFocused ? 'pulse-border' : ''}`}
              style={{ minWidth: '300px' }}
            >
              <div className="terminal-content p-sm">
                <div className="terminal-prompt">
                  <Search size={16} className="text-glow mr-sm" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={handleSearch}
                    onFocus={() => setIsSearchFocused(true)}
                    onBlur={() => setIsSearchFocused(false)}
                    placeholder="SEARCH TOPICS..."
                    className="terminal-input"
                    aria-label="Search topics"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Command Line Info */}
        <div className="mt-md">
          <div className="terminal-output">
            <div className="terminal-line info">
              <span className="terminal-line-prefix">$</span>
              <span className="terminal-line-content">
                {searchQuery ? 
                  `search --query="${searchQuery}" --database=fitness_library` :
                  'ready for command input...'
                }
                <span className="terminal-cursor">_</span>
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="flex gap-lg mt-md text-sm">
          <div className="flex items-center gap-sm">
            <span className="text-muted">TOPICS:</span>
            <span className="text-primary">574</span>
          </div>
          <div className="flex items-center gap-sm">
            <span className="text-muted">CATEGORIES:</span>
            <span className="text-primary">23</span>
          </div>
          <div className="flex items-center gap-sm">
            <span className="text-muted">CITATIONS:</span>
            <span className="text-primary">5,914+</span>
          </div>
          <div className="flex items-center gap-sm">
            <span className="text-muted">STATUS:</span>
            <span className="text-glow">ENHANCED</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;