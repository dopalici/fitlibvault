import React from 'react';
import { Lock, Check, ArrowRight, X } from 'lucide-react';
import { createCheckoutSession, PREMIUM_TIER } from '../lib/stripeService';

interface PremiumPaywallProps {
  userId?: string;
  isVisible?: boolean;
  onClose?: () => void;
}

export const PremiumPaywall: React.FC<PremiumPaywallProps> = ({ userId, isVisible = true, onClose }) => {
  if (!isVisible) return null;

  const handleSubscribe = async (tier: 'monthly' | 'annual') => {
    const priceId = tier === 'monthly' ? PREMIUM_TIER.MONTHLY : PREMIUM_TIER.ANNUAL;
    try {
      await createCheckoutSession(priceId, userId || 'anonymous');
    } catch (error) {
      console.error('Checkout failed:', error);
      alert('Failed to redirect to checkout');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-2xl w-full mx-4">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Lock className="w-6 h-6 text-blue-500" />
            <h2 className="text-2xl font-bold text-white">Upgrade to Premium</h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
          )}
        </div>

        <p className="text-slate-300 mb-8">
          Access all 500+ research topics, unlimited search, and exclusive features.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Monthly */}
          <div className="border border-slate-700 rounded-xl p-6 hover:border-blue-500 transition">
            <h3 className="text-xl font-bold text-white mb-2">Monthly</h3>
            <div className="text-3xl font-bold text-blue-500 mb-4">$7.99<span className="text-sm text-slate-400">/mo</span></div>
            <ul className="space-y-2 mb-6">
              {['All 500+ topics', 'Unlimited search', 'PDF export', 'Citation exporter'].map(feature => (
                <li key={feature} className="flex items-center gap-2 text-slate-300">
                  <Check className="w-4 h-4 text-green-500" />
                  {feature}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleSubscribe('monthly')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              Subscribe <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Annual */}
          <div className="border border-blue-500 bg-blue-500/10 rounded-xl p-6 ring-1 ring-blue-500">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xl font-bold text-white">Annual</h3>
              <span className="bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded">Save 20%</span>
            </div>
            <div className="text-3xl font-bold text-blue-500 mb-4">$79<span className="text-sm text-slate-400">/year</span></div>
            <ul className="space-y-2 mb-6">
              {['All 500+ topics', 'Unlimited search', 'PDF export', 'Citation exporter', 'Priority support'].map(feature => (
                <li key={feature} className="flex items-center gap-2 text-slate-300">
                  <Check className="w-4 h-4 text-green-500" />
                  {feature}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleSubscribe('annual')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition flex items-center justify-center gap-2"
            >
              Subscribe <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-center text-slate-400 text-sm">
          30-day money-back guarantee. Cancel anytime.
        </p>
      </div>
    </div>
  );
};
