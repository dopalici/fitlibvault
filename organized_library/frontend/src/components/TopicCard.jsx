import React from 'react';
import { Clock, BookOpen, Link2, Star, ArrowRight, Hash, Zap } from 'lucide-react';

const TopicCard = ({ topic, onTopicClick, showConnections = true }) => {
  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '#39d353';
      case 'intermediate': return '#ffbd2e';
      case 'advanced': return '#ff5f56';
      default: return '#08f7fe';
    }
  };

  const getDifficultyIcon = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '●';
      case 'intermediate': return '●●';
      case 'advanced': return '●●●';
      default: return '○';
    }
  };

  return (
    <div className="card hover-glow terminal-window slide-in-up" onClick={() => onTopicClick(topic.id)}>
      <div className="terminal-header">
        <div className="terminal-buttons">
          <div className="terminal-button close"></div>
          <div className="terminal-button minimize"></div>
          <div className="terminal-button maximize"></div>
        </div>
        <div className="terminal-title">{topic.id.toUpperCase()}</div>
      </div>
      
      <div className="terminal-content">
        {/* Topic Header */}
        <div className="flex items-start justify-between mb-sm">
          <h3 className="text-lg text-glow m-0 flex-1">{topic.title}</h3>
          <div className="flex items-center gap-xs ml-sm">
            <Star size={14} className="text-muted hover:text-glow cursor-pointer" />
            <span 
              className="text-xs px-xs py-xs rounded border"
              style={{ 
                color: getDifficultyColor(topic.difficulty),
                borderColor: getDifficultyColor(topic.difficulty) + '40'
              }}
            >
              {getDifficultyIcon(topic.difficulty)} {topic.difficulty.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Quick Takeaway */}
        <div className="mb-md">
          <div className="terminal-output">
            <div className="terminal-line info">
              <span className="terminal-line-prefix">></span>
              <span className="terminal-line-content text-sm">
                {topic.quickTakeaway}
              </span>
            </div>
          </div>
        </div>

        {/* Key Points Preview */}
        <div className="mb-md">
          <h4 className="text-sm text-glow mb-xs">KEY POINTS:</h4>
          <div className="terminal-output">
            {topic.keyPoints.slice(0, 3).map((point, index) => (
              <div key={index} className="terminal-line">
                <span className="terminal-line-prefix">•</span>
                <span className="terminal-line-content text-sm text-secondary">
                  {point}
                </span>
              </div>
            ))}
            {topic.keyPoints.length > 3 && (
              <div className="terminal-line">
                <span className="terminal-line-prefix">+</span>
                <span className="terminal-line-content text-sm text-muted">
                  {topic.keyPoints.length - 3} more points...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Topic Metadata */}
        <div className="flex items-center justify-between text-xs text-muted mb-md">
          <div className="flex items-center gap-md">
            <div className="flex items-center gap-xs">
              <Clock size={12} />
              <span>{topic.readingTime}</span>
            </div>
            <div className="flex items-center gap-xs">
              <BookOpen size={12} />
              <span>{topic.citationCount} citations</span>
            </div>
            {showConnections && (
              <div className="flex items-center gap-xs">
                <Link2 size={12} />
                <span>{topic.connections.length} connections</span>
              </div>
            )}
          </div>
          <div className="text-muted">
            Updated: {new Date(topic.lastUpdated).toLocaleDateString()}
          </div>
        </div>

        {/* Tags */}
        <div className="mb-md">
          <div className="flex flex-wrap gap-xs">
            {topic.tags.slice(0, 4).map((tag, index) => (
              <span 
                key={index}
                className="text-xs px-xs py-xs border border-muted text-muted hover:border-glow hover:text-glow transition-all cursor-pointer"
              >
                <Hash size={10} className="inline mr-xs" />
                {tag}
              </span>
            ))}
            {topic.tags.length > 4 && (
              <span className="text-xs text-muted">
                +{topic.tags.length - 4} more
              </span>
            )}
          </div>
        </div>

        {/* Connection Preview */}
        {showConnections && topic.connections.length > 0 && (
          <div className="mb-md">
            <h4 className="text-sm text-glow mb-xs">CONNECTED TO:</h4>
            <div className="terminal-output">
              {topic.connections.slice(0, 2).map((connectionId, index) => (
                <div key={index} className="terminal-line">
                  <span className="terminal-line-prefix">→</span>
                  <span className="terminal-line-content text-sm text-secondary hover:text-glow cursor-pointer">
                    {connectionId.replace('-', ' ').toUpperCase()}
                  </span>
                </div>
              ))}
              {topic.connections.length > 2 && (
                <div className="terminal-line">
                  <span className="terminal-line-prefix">+</span>
                  <span className="terminal-line-content text-sm text-muted">
                    {topic.connections.length - 2} more connections
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Action Button */}
        <div className="terminal-progress mb-sm">
          <div className="terminal-progress-bar" style={{ width: '0%' }}></div>
        </div>
        
        <button className="btn btn-primary w-full flex items-center justify-center gap-sm">
          <Zap size={14} />
          <span>ACCESS TOPIC</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default TopicCard;