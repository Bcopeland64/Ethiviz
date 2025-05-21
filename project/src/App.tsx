import React, { useState } from 'react';
import { Menu, X, Settings, Upload, Image as ImageIcon, FileText, ChevronDown, Search, Sparkles } from 'lucide-react';
import ConfigPanel from './components/ConfigPanel';
import MainContent from './components/MainContent';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-lg bg-white/80">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative group"
            >
              <div className="absolute inset-0 bg-blue-500/10 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                <Sparkles className="text-white" size={20} />
              </div>
              <h1 className="text-xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                Analysis Dashboard
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative group">
              <div className="absolute inset-0 bg-blue-500/5 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="search"
                placeholder="Search analysis..."
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-transparent relative transition-all duration-300 w-48 focus:w-64"
              />
            </div>
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-all duration-300 relative group">
              <div className="absolute inset-0 bg-blue-500/10 rounded-lg scale-0 group-hover:scale-100 transition-transform duration-300"></div>
              <Settings size={20} className="text-gray-600 transition-transform duration-300 group-hover:rotate-90" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <ConfigPanel isOpen={sidebarOpen} />

        {/* Main Content */}
        <MainContent sidebarOpen={sidebarOpen} />
      </div>
    </div>
  );
}

export default App;