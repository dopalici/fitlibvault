// Sample topic data structure for the fitness library
// This will eventually be replaced with API calls to your backend

export const categories = [
  {
    id: 'foundation',
    name: 'Foundation',
    description: 'Exercise science fundamentals, physiology, and biomechanics',
    icon: '🧬',
    fileCount: 66,
    color: '#08f7fe'
  },
  {
    id: 'resistance_training',
    name: 'Resistance Training',
    description: 'Training methods, equipment, and programming',
    icon: '💪',
    fileCount: 71,
    color: '#06d3d7'
  },
  {
    id: 'nutrition_diet',
    name: 'Nutrition & Diet',
    description: 'Sports nutrition, supplements, and dietary strategies',
    icon: '🥗',
    fileCount: 107,
    color: '#048b8f'
  },
  {
    id: 'exercise_library',
    name: 'Exercise Library',
    description: 'Detailed exercise technique instructions',
    icon: '📚',
    fileCount: 100,
    color: '#00ffff'
  },
  {
    id: 'performance_factors',
    name: 'Performance Factors',
    description: 'Testing, optimization, and psychology',
    icon: '📊',
    fileCount: 35,
    color: '#08f7fe'
  },
  {
    id: 'sports_specific',
    name: 'Sports Specific',
    description: 'Sport-specific training applications',
    icon: '⚽',
    fileCount: 31,
    color: '#06d3d7'
  }
];

export const sampleTopics = [
  {
    id: 'a1-energy-balance',
    title: 'Energy Balance',
    category: 'foundation',
    description: 'Understanding the fundamental principle of energy intake vs. energy expenditure',
    connections: ['a2-bmr-tdee', 'a3-macronutrients', 'c1-caloric-targets'],
    tags: ['fundamentals', 'nutrition', 'metabolism'],
    lastUpdated: '2025-06-05',
    citationCount: 8,
    readingTime: '12 min',
    difficulty: 'beginner',
    quickTakeaway: 'Energy balance is the relationship between calories consumed and calories burned, forming the foundation of all body composition changes.',
    keyPoints: [
      'Energy balance determines weight gain, loss, or maintenance',
      'Calories in vs. calories out is the fundamental equation',
      'Small daily deficits create sustainable fat loss',
      'Energy balance varies based on individual factors',
      'Understanding NEAT is crucial for accurate calculations'
    ]
  },
  {
    id: 'b1-progressive-overload',
    title: 'Progressive Overload',
    category: 'resistance_training',
    description: 'The principle of gradually increasing training demands over time',
    connections: ['a19-principle-overload', 'b3-hypertrophy', 'b4-strength-training'],
    tags: ['training principles', 'progression', 'adaptation'],
    lastUpdated: '2025-06-05',
    citationCount: 12,
    readingTime: '15 min',
    difficulty: 'intermediate',
    quickTakeaway: 'Progressive overload means gradually increasing training demands—weight, reps, sets, or frequency—to ensure continued muscle adaptation.',
    keyPoints: [
      'Systematic increases in training variables',
      'Multiple methods: weight, reps, sets, frequency',
      'Double progression strategy recommended',
      'Individual progression rates vary significantly',
      'Deload periods prevent plateaus and overtraining'
    ]
  },
  {
    id: 'c1-caloric-targets',
    title: 'Caloric Targets for Different Goals',
    category: 'nutrition_diet',
    description: 'Setting appropriate caloric intake based on individual goals and circumstances',
    connections: ['a1-energy-balance', 'a2-bmr-tdee', 'c7-weight-management'],
    tags: ['nutrition planning', 'goal setting', 'calories'],
    lastUpdated: '2025-06-05',
    citationCount: 15,
    readingTime: '18 min',
    difficulty: 'intermediate',
    quickTakeaway: 'Caloric targets must be individualized based on goals, activity level, and metabolic factors for optimal results.',
    keyPoints: [
      'Fat loss: 300-750 calorie deficit from TDEE',
      'Muscle gain: 200-500 calorie surplus from TDEE',
      'Maintenance: Match calories to TDEE',
      'Adjust based on progress and adherence',
      'Consider metabolic adaptation over time'
    ]
  }
];

export const topicConnections = [
  {
    from: 'a1-energy-balance',
    to: 'a2-bmr-tdee',
    type: 'prerequisite',
    strength: 0.9
  },
  {
    from: 'a1-energy-balance',
    to: 'c1-caloric-targets',
    type: 'application',
    strength: 0.8
  },
  {
    from: 'b1-progressive-overload',
    to: 'a19-principle-overload',
    type: 'foundation',
    strength: 0.9
  },
  {
    from: 'b1-progressive-overload',
    to: 'b3-hypertrophy',
    type: 'application',
    strength: 0.7
  }
];

// Search functionality
export const searchTopics = (query, topics = sampleTopics) => {
  if (!query) return topics;
  
  const searchTerms = query.toLowerCase().split(' ');
  
  return topics.filter(topic => {
    const searchContent = [
      topic.title,
      topic.description,
      topic.quickTakeaway,
      ...topic.tags,
      ...topic.keyPoints
    ].join(' ').toLowerCase();
    
    return searchTerms.every(term => searchContent.includes(term));
  });
};

// Get related topics
export const getRelatedTopics = (topicId, connections = topicConnections, topics = sampleTopics) => {
  const relatedIds = connections
    .filter(conn => conn.from === topicId || conn.to === topicId)
    .map(conn => conn.from === topicId ? conn.to : conn.from);
  
  return topics.filter(topic => relatedIds.includes(topic.id));
};

// Get topics by category
export const getTopicsByCategory = (categoryId, topics = sampleTopics) => {
  return topics.filter(topic => topic.category === categoryId);
};

// Generate breadcrumb navigation
export const generateBreadcrumbs = (topicId, topics = sampleTopics, categories) => {
  const topic = topics.find(t => t.id === topicId);
  if (!topic) return [];
  
  const category = categories.find(c => c.id === topic.category);
  
  return [
    { name: 'Library', path: '/' },
    { name: category?.name || 'Unknown', path: `/category/${topic.category}` },
    { name: topic.title, path: `/topic/${topicId}` }
  ];
};

// Get topic statistics
export const getTopicStats = (topics = sampleTopics) => {
  return {
    totalTopics: topics.length,
    totalCitations: topics.reduce((sum, topic) => sum + topic.citationCount, 0),
    averageReadingTime: Math.round(
      topics.reduce((sum, topic) => sum + parseInt(topic.readingTime), 0) / topics.length
    ),
    categories: [...new Set(topics.map(topic => topic.category))].length,
    lastUpdated: new Date(Math.max(...topics.map(topic => new Date(topic.lastUpdated)))).toISOString().split('T')[0]
  };
};

// Filter topics by difficulty
export const filterByDifficulty = (difficulty, topics = sampleTopics) => {
  return topics.filter(topic => topic.difficulty === difficulty);
};

// Get recent updates
export const getRecentUpdates = (days = 30, topics = sampleTopics) => {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  
  return topics
    .filter(topic => new Date(topic.lastUpdated) >= cutoffDate)
    .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));
};

// Mock API simulation
export const mockApi = {
  getTopics: (params = {}) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        let results = [...sampleTopics];
        
        if (params.category) {
          results = getTopicsByCategory(params.category, results);
        }
        
        if (params.search) {
          results = searchTopics(params.search, results);
        }
        
        if (params.difficulty) {
          results = filterByDifficulty(params.difficulty, results);
        }
        
        resolve({
          topics: results,
          totalCount: results.length,
          page: params.page || 1,
          pageSize: params.pageSize || 20
        });
      }, 300); // Simulate network delay
    });
  },
  
  getTopic: (id) => {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const topic = sampleTopics.find(t => t.id === id);
        if (topic) {
          resolve({
            ...topic,
            fullContent: `This is the complete content for ${topic.title}. In a real implementation, this would contain the full markdown content with research citations, practical applications, and detailed explanations.`,
            relatedTopics: getRelatedTopics(id)
          });
        } else {
          reject(new Error('Topic not found'));
        }
      }, 200);
    });
  },
  
  getCategories: () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(categories);
      }, 100);
    });
  }
};