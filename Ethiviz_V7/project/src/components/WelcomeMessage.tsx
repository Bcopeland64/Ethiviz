import React from 'react';
import { Sparkles, ArrowRight, Zap, ChevronRight } from 'lucide-react';

function WelcomeMessage() {
  return (
    <div className="max-w-4xl mx-auto text-center">
      <div className="relative mb-16">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/30 to-purple-600/30 blur-3xl rounded-full transform -translate-y-1/2"></div>
        <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 w-24 h-24 rounded-3xl flex items-center justify-center mx-auto mb-8 transform rotate-12 hover:rotate-0 transition-all duration-500 hover:scale-110 shadow-xl hover:shadow-2xl group">
          <Sparkles className="text-white transform group-hover:scale-110 transition-transform duration-300" size={40} />
        </div>
      </div>

      <div className="relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 to-purple-600/20 blur-2xl"></div>
        <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl p-8 shadow-xl">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-8 leading-tight">
            Welcome to Analysis Dashboard
          </h1>
          <p className="text-xl text-gray-600 mb-12 leading-relaxed max-w-2xl mx-auto">
            Get started by configuring your analysis parameters in the sidebar and uploading your data.
            Our advanced algorithms will help you uncover meaningful insights from your content.
          </p>
          
          <div className="flex justify-center gap-6 mb-12">
            <button className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-medium transition-all duration-300 hover:shadow-lg hover:scale-105 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>
              <span className="relative">Start Analysis</span>
              <Zap className="relative transform transition-all duration-300 group-hover:rotate-12 group-hover:scale-110" size={18} />
            </button>
            <button className="group px-8 py-4 text-blue-500 rounded-xl font-medium transition-all duration-300 hover:bg-blue-50 relative overflow-hidden">
              <span className="relative flex items-center gap-2">
                Learn More
                <ChevronRight className="transform transition-transform duration-300 group-hover:translate-x-1" size={18} />
              </span>
            </button>
          </div>

          <div className="relative group">
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl blur transition-all duration-500 group-hover:blur-xl opacity-70"></div>
            <div className="relative overflow-hidden rounded-2xl">
              <img
                src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1200"
                alt="Data Analysis Illustration"
                className="w-full transform transition-all duration-700 group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WelcomeMessage;