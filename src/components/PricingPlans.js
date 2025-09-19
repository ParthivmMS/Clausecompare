import React from 'react';

export default function PricingPlans() {
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Choose Your Plan</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border rounded p-4">
          <h3 className="font-semibold">Free Plan</h3>
          <p>Basic contract comparison for personal use.</p>
          <p className="font-bold">$0/month</p>
        </div>

        <div className="border rounded p-4">
          <h3 className="font-semibold">Pro Plan</h3>
          <p>Advanced features, API access, priority support.</p>
          <p className="font-bold">$49/month</p>
        </div>

        <div className="border rounded p-4">
          <h3 className="font-semibold">Enterprise</h3>
          <p>Custom solutions for large teams and businesses.</p>
          <p className="font-bold">Contact us</p>
        </div>
      </div>
    </div>
  );
}
