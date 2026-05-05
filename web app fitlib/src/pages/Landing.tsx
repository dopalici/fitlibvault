import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Sparkles, 
  Target, 
  BookOpen, 
  Users, 
  ChevronRight, 
  Check,
  Brain,
  TrendingUp,
  Award,
  Flame,
  ArrowRight,
  Globe,
  Lock,
  Zap
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../lib/utils';
import { PremiumPaywall } from '../components/PremiumPaywall';

const HERO_STATS = [
  { value: "2,000+", label: "Research Papers" },
  { value: "15+", label: "Expert Authors" },
  { value: "50K+", label: "Hours Saved" },
  { value: "98%", label: "Accuracy Rate" }
];

const FEATURES = [
  {
    icon: Brain,
    title: "Evidence-Based Knowledge",
    description: "Every claim backed by peer-reviewed research and expert analysis.",
    color: "text-blue-500"
  },
  {
    icon: Target,
    title: "Structured Learning Path",
    description: "Progressive curriculum from foundations to advanced concepts.",
    color: "text-green-500"
  },
  {
    icon: TrendingUp,
    title: "Track Your Progress",
    description: "Monitor completion rates, streaks, and knowledge mastery.",
    color: "text-purple-500"
  },
  {
    icon: Users,
    title: "Expert Curated",
    description: "Content reviewed by leading researchers and practitioners.",
    color: "text-orange-500"
  }
];

const TESTIMONIALS = [
  {
    name: "Dr. Sarah Chen",
    role: "Sports Scientist",
    content: "FitLib has revolutionized how I stay current with exercise science research. The structured format saves me hours of reading.",
    avatar: "🧑‍🔬"
  },
  {
    name: "Marcus Rodriguez",
    role: "Certified Trainer",
    content: "My clients get better results because I can confidently apply the latest evidence-based practices from FitLib.",
    avatar: "💪"
  },
  {
    name: "Lisa Thompson",
    role: "Nutrition Coach",
    content: "The nutrition modules are incredibly detailed yet digestible. Perfect for staying ahead in this rapidly evolving field.",
    avatar: "🥗"
  }
];

export const Landing: React.FC = () => {
  const [showPaywall, setShowPaywall] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(20)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-blue-500/30 rounded-full"
              animate={{
                x: [0, Math.random() * 1000],
                y: [0, Math.random() * 800],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: Math.random() * 10 + 10,
                repeat: Infinity,
                delay: Math.random() * 5,
              }}
            />
          ))}
        </div>

        <div className="relative z-10 text-center max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-2 mb-6">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-semibold text-blue-400">Evidence-Based Fitness Knowledge</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-black mb-6 leading-tight">
              Master <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Exercise Science</span><br />
              With Confidence
            </h1>
            
            <p className="text-xl md:text-2xl text-slate-400 mb-8 max-w-4xl mx-auto leading-relaxed">
              Stop wasting time on conflicting fitness advice. Access 2,000+ research papers transformed into 
              actionable knowledge by leading experts in exercise physiology, nutrition, and sports science.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          >
            <button 
              onClick={() => setShowPaywall(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-2xl shadow-blue-500/25 transition-all hover:scale-105 flex items-center gap-2 justify-center"
            >
              Start Learning Now
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <Link 
              to="/library"
              className="border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white px-8 py-4 rounded-xl font-bold text-lg transition-all hover:scale-105 flex items-center gap-2 justify-center"
            >
              Explore Free Content
              <BookOpen className="w-5 h-5" />
            </Link>
          </motion.div>

          {/* Hero Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
          >
            {HERO_STATS.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-black text-white mb-2">{stat.value}</div>
                <div className="text-sm text-slate-400 font-semibold">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black mb-6">
              Why Choose <span className="text-blue-400">FitLib</span>?
            </h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              We bridge the gap between cutting-edge research and practical application, 
              giving you the confidence to make evidence-based decisions.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {FEATURES.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                className="group p-8 bg-slate-900/50 border border-slate-800 rounded-2xl hover:border-blue-500/50 transition-all duration-300 hover:-translate-y-2"
              >
                <div className={cn("w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform", 
                  feature.color.replace('text', 'bg').replace('500', '500/10'))}>
                  <feature.icon className={cn("w-6 h-6", feature.color)} />
                </div>
                <h3 className="text-xl font-bold mb-3 group-hover:text-blue-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black mb-6">
              Trusted by <span className="text-green-400">Industry Leaders</span>
            </h2>
            <p className="text-xl text-slate-400">
              Join thousands of professionals who rely on FitLib for accurate, up-to-date information.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            {TESTIMONIALS.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                className="p-8 bg-slate-900/80 border border-slate-800 rounded-2xl"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="text-3xl">{testimonial.avatar}</div>
                  <div>
                    <h4 className="font-bold text-white">{testimonial.name}</h4>
                    <p className="text-slate-400 text-sm">{testimonial.role}</p>
                  </div>
                </div>
                <p className="text-slate-300 leading-relaxed italic">
                  "{testimonial.content}"
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-5xl font-black mb-6">
              Simple, <span className="text-blue-400">Transparent</span> Pricing
            </h2>
            <p className="text-xl text-slate-400 mb-12">
              Less than the cost of a single research journal subscription. 
              Get access to our entire curated library.
            </p>

            <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto">
              {/* Monthly */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="p-8 bg-slate-900/50 border border-slate-800 rounded-2xl"
              >
                <h3 className="text-2xl font-bold mb-4">Monthly</h3>
                <div className="text-4xl font-black mb-6">
                  $7.99<span className="text-slate-400 text-lg font-normal">/month</span>
                </div>
                <ul className="space-y-3 mb-8 text-left">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Full library access</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Progress tracking</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Regular updates</span>
                  </li>
                </ul>
                <button
                  onClick={() => setShowPaywall(true)}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-white px-6 py-3 rounded-xl font-bold transition-all"
                >
                  Get Started
                </button>
              </motion.div>

              {/* Annual */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="p-8 bg-gradient-to-br from-blue-600/20 to-purple-600/20 border-2 border-blue-500/50 rounded-2xl relative"
              >
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                  Best Value
                </div>
                <h3 className="text-2xl font-bold mb-4">Annual</h3>
                <div className="text-4xl font-black mb-2">
                  $79<span className="text-slate-400 text-lg font-normal">/year</span>
                </div>
                <div className="text-green-400 text-sm font-semibold mb-4">Save $16.88</div>
                <ul className="space-y-3 mb-8 text-left">
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Everything in Monthly</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Priority support</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <Check className="w-5 h-5 text-green-400" />
                    <span>Exclusive content</span>
                  </li>
                </ul>
                <button
                  onClick={() => setShowPaywall(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-xl shadow-blue-500/25"
                >
                  Get Started
                </button>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-gradient-to-r from-blue-900/20 to-purple-900/20">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-5xl font-black mb-6">
              Ready to Master Exercise Science?
            </h2>
            <p className="text-xl text-slate-400 mb-8">
              Join the community of evidence-based fitness professionals who trust FitLib 
              to stay ahead of the curve.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => setShowPaywall(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-2xl shadow-blue-500/25 transition-all hover:scale-105 flex items-center gap-2 justify-center"
              >
                Start Your Journey
                <Zap className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Premium Paywall Modal */}
      {showPaywall && (
        <PremiumPaywall onClose={() => setShowPaywall(false)} />
      )}
    </div>
  );
};