"use client";
import { useState, useEffect } from 'react';
import axios from 'axios';
import EnvGenerator from '../components/EnvGenerator';

export default function Dashboard() {
  const [licenses, setLicenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenerator, setShowGenerator] = useState(false);
  const [selectedKey, setSelectedKey] = useState('');

  const AUTH_SERVER_URL = process.env.NEXT_PUBLIC_AUTH_SERVER_URL || 'http://localhost:8000';

  const fetchLicenses = async () => {
    // This would normally be a list endpoint, but I'll assume we have one or just use a mock for now
    // Since I didn't add a LIST endpoint in FastAPI, let me add it.
    try {
      // const res = await axios.get(`${AUTH_SERVER_URL}/licenses`);
      // setLicenses(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateLicense = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await axios.post(`${AUTH_SERVER_URL}/license/generate`, {
        owner_id: formData.get('owner_id'),
        days: parseInt(formData.get('days') as string),
      });
      fetchLicenses();
    } catch (err) {
      alert('Error generating license');
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Bot Licensing Admin</h1>
      
      <section className="mb-12 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Generate New License</h2>
        <form onSubmit={generateLicense} className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium">Owner Telegram ID</label>
            <input name="owner_id" className="border p-2 rounded" required />
          </div>
          <div>
            <label className="block text-sm font-medium">Duration (Days)</label>
            <input name="days" type="number" defaultValue="30" className="border p-2 rounded" required />
          </div>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Generate & Send
          </button>
        </form>
      </section>

      {showGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white p-8 rounded-lg w-full max-w-md">
            <button onClick={() => setShowGenerator(false)} className="float-right text-gray-500">Close</button>
            <EnvGenerator licenseKey={selectedKey} />
          </div>
        </div>
      )}

      <button 
        onClick={() => setShowGenerator(true)} 
        className="mb-4 bg-green-600 text-white px-4 py-2 rounded"
      >
        Open .env Generator
      </button>

      {/* License table would go here */}
    </div>
  );
}
