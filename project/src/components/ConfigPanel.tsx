import React, { useState } from 'react';
import { Upload, Image as ImageIcon, FileText, ChevronDown, Settings, Beaker, FileOutput, Wand2, Zap } from 'lucide-react';

interface ConfigPanelProps {
  isOpen: boolean;
}

function ConfigPanel({ isOpen }: ConfigPanelProps) {
  const [selectedDataInput, setSelectedDataInput] = useState<'own' | 'sample' | 'none'>('none');
  const [expandedOption, setExpandedOption] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    // Handle file drop logic here
  };

  return (
    <div 
      className={`${isOpen ? 'w-80' : 'w-0'} transition-all duration-500 overflow-hidden bg-white border-r border-gray-200 shadow-lg relative`}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-transparent to-purple-50/50 pointer-events-none"></div>
      <div className="p-6 relative">
        <div className="space-y-8">
          {/* Analysis Type */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Wand2 size={14} className="text-blue-500" />
              Analysis Type
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <button className="group relative flex flex-col items-center p-4 border-2 border-blue-500 rounded-xl bg-blue-50 transition-all duration-300 hover:shadow-xl hover:scale-[1.02]">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-blue-50 rounded-xl transform scale-0 group-hover:scale-100 transition-transform duration-300"></div>
                <FileText className="relative text-blue-500 mb-2 transform transition-transform group-hover:scale-110 group-hover:rotate-6" />
                <span className="relative text-sm font-medium text-blue-700">Text</span>
              </button>
              <button className="group relative flex flex-col items-center p-4 border-2 border-gray-200 rounded-xl transition-all duration-300 hover:shadow-xl hover:scale-[1.02]">
                <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-white rounded-xl transform scale-0 group-hover:scale-100 transition-transform duration-300"></div>
                <ImageIcon className="relative text-gray-400 mb-2 transform transition-transform group-hover:scale-110 group-hover:rotate-6" />
                <span className="relative text-sm font-medium text-gray-600">Image</span>
              </button>
            </div>
          </div>

          {/* Data Input */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Upload size={14} className="text-blue-500" />
              Data Input
            </h2>
            <div className="space-y-3">
              <button
                onClick={() => setSelectedDataInput('own')}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                  selectedDataInput === 'own'
                    ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-[1.02]'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 hover:shadow-md hover:scale-[1.01]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className={`text-sm font-medium ${
                      selectedDataInput === 'own' ? 'text-blue-700' : 'text-gray-700'
                    }`}>Add your own data</h3>
                    <p className="text-xs text-gray-500 mt-1">Upload your custom dataset</p>
                  </div>
                  <Upload size={18} className={`transform transition-all duration-300 ${
                    selectedDataInput === 'own' ? 'text-blue-500 scale-110 rotate-6' : 'text-gray-400'
                  }`} />
                </div>
                {selectedDataInput === 'own' && (
                  <div 
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`mt-4 border-2 border-dashed rounded-xl p-6 text-center transition-all duration-300 ${
                      isDragging 
                        ? 'border-blue-500 bg-blue-50 scale-[1.02] shadow-lg' 
                        : 'border-gray-300 hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    <Upload className={`mx-auto mb-3 transition-all duration-300 ${
                      isDragging ? 'text-blue-500 animate-bounce' : 'text-gray-400 hover:text-blue-500'
                    }`} />
                    <p className="text-sm text-gray-600">
                      Drag and drop your files here or{' '}
                      <button className="text-blue-500 hover:text-blue-600 font-medium underline decoration-dotted underline-offset-2">
                        browse
                      </button>
                    </p>
                    {isDragging && (
                      <div className="absolute inset-0 bg-blue-500/5 rounded-xl pointer-events-none"></div>
                    )}
                  </div>
                )}
              </button>

              <button
                onClick={() => setSelectedDataInput('sample')}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                  selectedDataInput === 'sample'
                    ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-[1.02]'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 hover:shadow-md hover:scale-[1.01]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className={`text-sm font-medium ${
                      selectedDataInput === 'sample' ? 'text-blue-700' : 'text-gray-700'
                    }`}>Use sample data</h3>
                    <p className="text-xs text-gray-500 mt-1">Try with our pre-loaded dataset</p>
                  </div>
                  <FileText size={18} className={`transform transition-all duration-300 ${
                    selectedDataInput === 'sample' ? 'text-blue-500 scale-110 rotate-6' : 'text-gray-400'
                  }`} />
                </div>
              </button>

              <button
                onClick={() => setSelectedDataInput('none')}
                className={`w-full p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                  selectedDataInput === 'none'
                    ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-[1.02]'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50 hover:shadow-md hover:scale-[1.01]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className={`text-sm font-medium ${
                      selectedDataInput === 'none' ? 'text-blue-700' : 'text-gray-700'
                    }`}>None</h3>
                    <p className="text-xs text-gray-500 mt-1">Configure without data</p>
                  </div>
                  <ChevronDown size={18} className={`transform transition-all duration-300 ${
                    selectedDataInput === 'none' ? 'text-blue-500 scale-110 rotate-180' : 'text-gray-400'
                  }`} />
                </div>
              </button>
            </div>
          </div>

          {/* Traditions */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Settings size={14} className="text-blue-500" />
              Traditions
            </h2>
            <button className="w-full flex items-center justify-between p-4 border-2 border-gray-200 rounded-xl transition-all duration-300 hover:border-blue-300 hover:bg-blue-50 hover:shadow-md hover:scale-[1.01] group">
              <span className="text-sm text-gray-700 group-hover:text-blue-600">Select traditions</span>
              <ChevronDown size={16} className="text-gray-400 transition-transform duration-300 group-hover:rotate-180 group-hover:text-blue-500" />
            </button>
          </div>

          {/* Advanced Options */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Beaker size={14} className="text-blue-500" />
              Advanced Options
            </h2>
            <div className="space-y-2 rounded-xl overflow-hidden border-2 border-gray-200 transition-all duration-300 hover:border-blue-200">
              <button
                onClick={() => setExpandedOption(expandedOption === 'processing' ? null : 'processing')}
                className="w-full p-4 text-left transition-all duration-300 hover:bg-blue-50 focus:outline-none group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Settings size={16} className="text-gray-400 group-hover:text-blue-500 transition-colors duration-300" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600 transition-colors duration-300">Processing Settings</span>
                  </div>
                  <ChevronDown
                    size={16}
                    className={`text-gray-400 transform transition-transform duration-300 group-hover:text-blue-500 ${
                      expandedOption === 'processing' ? 'rotate-180' : ''
                    }`}
                  />
                </div>
              </button>
              <button
                onClick={() => setExpandedOption(expandedOption === 'output' ? null : 'output')}
                className="w-full p-4 text-left transition-all duration-300 hover:bg-blue-50 focus:outline-none group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileOutput size={16} className="text-gray-400 group-hover:text-blue-500 transition-colors duration-300" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600 transition-colors duration-300">Output Format</span>
                  </div>
                  <ChevronDown
                    size={16}
                    className={`text-gray-400 transform transition-transform duration-300 group-hover:text-blue-500 ${
                      expandedOption === 'output' ? 'rotate-180' : ''
                    }`}
                  />
                </div>
              </button>
              <button
                onClick={() => setExpandedOption(expandedOption === 'parameters' ? null : 'parameters')}
                className="w-full p-4 text-left transition-all duration-300 hover:bg-blue-50 focus:outline-none group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Beaker size={16} className="text-gray-400 group-hover:text-blue-500 transition-colors duration-300" />
                    <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600 transition-colors duration-300">Analysis Parameters</span>
                  </div>
                  <ChevronDown
                    size={16}
                    className={`text-gray-400 transform transition-transform duration-300 group-hover:text-blue-500 ${
                      expandedOption === 'parameters' ? 'rotate-180' : ''
                    }`}
                  />
                </div>
              </button>
            </div>
          </div>

          {/* Run Button */}
          <button className="relative w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-4 rounded-xl font-medium transition-all duration-300 hover:shadow-xl hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>
            <div className="relative flex items-center justify-center gap-2">
              <Zap size={18} className="transform group-hover:rotate-12 transition-transform duration-300" />
              <span>Run Analysis</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfigPanel;