"use client";
import { useState } from 'react';
import axios from 'axios';

export default function EnvGenerator({ licenseKey: initialKey }: { licenseKey?: string }) {
  const [formData, setFormData] = useState({
    api_id: '',
    api_hash: '',
    bot_token: '',
    license_key: initialKey || '',
  });

  const AUTH_SERVER_URL = process.env.NEXT_PUBLIC_AUTH_SERVER_URL || 'http://localhost:8000';

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleDownload = async () => {
    if (!formData.license_key) return alert('License Key is required');

    try {
      // Save credentials to auth server (encrypted)
      await axios.post(`${AUTH_SERVER_URL}/license/${formData.license_key}/credentials`, {
        api_id: formData.api_id,
        api_hash: formData.api_hash,
        bot_token: formData.bot_token,
      });

      // Generate .env content
      const envContent = `API_ID=${formData.api_id}
API_HASH=${formData.api_hash}
BOT_TOKEN=${formData.bot_token}
LICENSE_KEY=${formData.license_key}
AUTH_SERVER_URL=${AUTH_SERVER_URL}
`;

      const blob = new Blob([envContent], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '.env';
      a.click();
    } catch (err) {
      alert('Error saving credentials to server');
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">.env Template Generator</h2>
      <div>
        <label className="block text-sm">License Key</label>
        <input name="license_key" value={formData.license_key} onChange={handleChange} className="w-full border p-2 rounded" />
      </div>
      <div>
        <label className="block text-sm">API ID</label>
        <input name="api_id" value={formData.api_id} onChange={handleChange} className="w-full border p-2 rounded" />
      </div>
      <div>
        <label className="block text-sm">API HASH</label>
        <input name="api_hash" value={formData.api_hash} onChange={handleChange} className="w-full border p-2 rounded" />
      </div>
      <div>
        <label className="block text-sm">BOT TOKEN</label>
        <input name="bot_token" value={formData.bot_token} onChange={handleChange} className="w-full border p-2 rounded" />
      </div>
      <button 
        onClick={handleDownload}
        className="w-full bg-blue-600 text-white py-2 rounded font-bold hover:bg-blue-700"
      >
        Save & Download .env
      </button>
    </div>
  );
}
