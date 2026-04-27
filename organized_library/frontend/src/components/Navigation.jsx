import React, { useState } from 'react';
import { ChevronRight, Folder, File, Hash, Clock, Star, ArrowRight } from 'lucide-react';
import { categories } from '../data/topicsData';

const Navigation = ({ isOpen, onCategorySelect, selectedCategory }) => {
  const [expandedCategories, setExpandedCategories] = useState({});

  const toggleCategory = (categoryId) => {
    setExpandedCategories(prev => ({
      ...prev,
      [categoryId]: !prev[categoryId]
    }));
  };

  const handleCategoryClick = (category) => {
    onCategorySelect(category.id);
    toggleCategory(category.id);
  };

  if (!isOpen) return null;

  return (
    <nav className="terminal-window fade-in">
      <div className="terminal-header">
        <div className="terminal-buttons">
          <div className="terminal-button close"></div>
          <div className="terminal-button minimize"></div>
          <div className="terminal-button maximize"></div>
        </div>
        <div className="terminal-title">NAVIGATION TREE</div>
      </div>
      
      <div className="terminal-content">
        {/* Navigation Header */}
        <div className="terminal-output mb-md">
          <div className="terminal-line info">
            <span className="terminal-line-prefix">├─</span>
            <span className="terminal-line-content">FITNESS_LIBRARY/</span>
          </div>
        </div>

        {/* Quick Navigation */}
        <div className="mb-lg">
          <h3 className="text-sm text-glow mb-sm">QUICK ACCESS</h3>
          <div className="grid grid-2 gap-sm">
            <button className="btn btn-primary text-left flex items-center gap-sm">
              <Star size={14} />
              <span>FAVORITES</span>
            </button>
            <button className="btn text-left flex items-center gap-sm">
              <Clock size={14} />
              <span>RECENT</span>
            </button>
          </div>
        </div>

        {/* Category Tree */}
        <div className="mb-lg">
          <h3 className="text-sm text-glow mb-sm">CATEGORIES</h3>
          <div className="space-y-xs">
            {categories.map((category, index) => (
              <div key={category.id} className="fade-in-delay-1">
                <button
                  onClick={() => handleCategoryClick(category)}
                  className={`w-full text-left p-sm hover-glow transition-all ${
                    selectedCategory === category.id ? 'bg-primary/10 border-glow' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-sm">
                      <ChevronRight 
                        size={12} 
                        className={`transition-transform ${
                          expandedCategories[category.id] ? 'rotate-90' : ''
                        }`}
                      />
                      <Folder size={14} className="text-glow" />
                      <span className="text-sm text-primary">{category.name}</span>
                    </div>
                    <div className="flex items-center gap-sm">
                      <span className="text-xs text-muted">{category.fileCount}</span>
                      <Hash size={10} className="text-muted" />
                    </div>
                  </div>
                </button>

                {/* Subcategory Preview */}
                {expandedCategories[category.id] && (
                  <div className="ml-lg mt-xs slide-in-right">
                    <div className="terminal-output">
                      <div className="terminal-line">
                        <span className="terminal-line-prefix">│  ├─</span>
                        <span className="terminal-line-content text-xs text-muted">
                          {category.description}
                        </span>
                      </div>
                      <div className="terminal-line">
                        <span className="terminal-line-prefix">│  ├─</span>
                        <span className="terminal-line-content text-xs">
                          <File size={10} className="inline mr-xs" />
                          {category.fileCount} topics available
                        </span>
                      </div>
                      <div className="terminal-line">
                        <span className="terminal-line-prefix">│  └─</span>
                        <span className="terminal-line-content text-xs text-glow">
                          <ArrowRight size={10} className="inline mr-xs" />
                          Click to explore
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* System Information */}
        <div className="border-t border-muted pt-md">
          <h3 className="text-sm text-glow mb-sm">SYSTEM INFO</h3>
          <div className="terminal-output">
            <div className="terminal-line">
              <span className="terminal-line-prefix">•</span>
              <span className="terminal-line-content text-xs">
                Version: 2.0.1-enhanced
              </span>
            </div>
            <div className="terminal-line">
              <span className="terminal-line-prefix">•</span>
              <span className="terminal-line-content text-xs">
                Database: 574 topics indexed
              </span>
            </div>
            <div className="terminal-line">
              <span className="terminal-line-prefix">•</span>
              <span className="terminal-line-content text-xs">
                Links: 5,914 cross-references
              </span>
            </div>
            <div className="terminal-line success">
              <span className="terminal-line-prefix">✓</span>
              <span className="terminal-line-content text-xs">
                All systems operational
              </span>
            </div>
          </div>
        </div>

        {/* Command Shortcuts */}
        <div className="border-t border-muted pt-md mt-md">
          <h3 className="text-sm text-glow mb-sm">SHORTCUTS</h3>
          <div className="command-list">
            <div className="command-item">
              <span className="command-name text-xs">Ctrl + K</span>
              <span className="command-description">Quick Search</span>
            </div>
            <div className="command-item">
              <span className="command-name text-xs">Ctrl + /</span>
              <span className="command-description">Command Palette</span>
            </div>
            <div className="command-item">
              <span className="command-name text-xs">ESC</span>
              <span className="command-description">Close Panel</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;