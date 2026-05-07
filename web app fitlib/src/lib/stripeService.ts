import { env, getApiUrl } from './env';

export async function createCheckoutSession(priceId: string, userId: string): Promise<void> {
  if (!env.stripePublicKey) {
    throw new Error('Missing VITE_STRIPE_PUBLIC_KEY');
  }

  const origin = window.location.origin;
  const response = await fetch(getApiUrl('/api/create-checkout-session'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      priceId,
      userId,
      successUrl: `${origin}/library?checkout=success`,
      cancelUrl: `${origin}/library?checkout=cancelled`,
    }),
  });

  if (!response.ok) {
    throw new Error('Unable to create checkout session');
  }

  const { checkoutUrl } = await response.json();
  if (!checkoutUrl) {
    throw new Error('Checkout URL missing from API response');
  }
  window.location.assign(checkoutUrl);
}

export async function verifySubscription(userId: string): Promise<{ premium: boolean; expiresAt?: Date }> {
  const response = await fetch(getApiUrl(`/api/check-subscription?userId=${encodeURIComponent(userId)}`));
  if (!response.ok) {
    throw new Error('Failed to verify subscription status');
  }
  const data = await response.json();
  return {
    premium: data.premium === true,
    expiresAt: data.expiresAt ? new Date(data.expiresAt) : undefined,
  };
}

export const PREMIUM_TIER = {
  MONTHLY: 'price_monthly_premium',
  ANNUAL: 'price_annual_premium',
};
