import React, { useState, useCallback, ChangeEvent } from 'react';
import axios from 'axios'; // Import axios
import { Upload, Image as ImageIcon, FileText, ChevronDown, Settings, Beaker, FileOutput, Wand2, Zap, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

// Define types for state
type AnalysisType = 'text' | 'image' | 'text_and_image' | null;
type DataSourceType = 'upload' | 'sample' | 'none'; // 'none' could be initial or if user deselects

const AVAILABLE_TRADITIONS = ['western', 'ubuntu', 'confucian', 'islamic'];
const API_BASE_URL = 'http://localhost:5001'; // Assuming Flask server runs on port 5001

interface ConfigPanelProps {
  isOpen: boolean;
  // Props to lift state up to App.tsx or context
  onAnalysisStart: () => void;
  onAnalysisComplete: (results: any) => void; // 'any' for now, replace with proper type
  onAnalysisError: (error: string) => void;
  setIsLoadingGlobal: (isLoading: boolean) => void; // To control global loading state
  setJobIdGlobal: (jobId: string | null) => void;
}

function ConfigPanel({ 
  isOpen, 
  onAnalysisStart, 
  onAnalysisComplete, 
  onAnalysisError,
  setIsLoadingGlobal, // Consume this prop
  setJobIdGlobal // Consume this prop
}: ConfigPanelProps) {
  const [analysisType, setAnalysisType] = useState<AnalysisType>(null);
  const [selectedTraditions, setSelectedTraditions] = useState<string[]>(AVAILABLE_TRADITIONS);
  const [textFile, setTextFile] = useState<File | null>(null);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [dataSourceType, setDataSourceType] = useState<DataSourceType>('none');
  
  // Advanced options can be a simple object for now
  const [advancedOptions, setAdvancedOptions] = useState<object>({
    text_advanced_options: { max_tokens: 10000, nlp_model: "en_core_web_sm"},
    image_advanced_options: { feature_level: "medium", batch_size: 16 }
  });

  // Local loading/error/job states for this panel, might be partly duplicated by global state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusUrl, setStatusUrl] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);


  const [expandedOption, setExpandedOption] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleAnalysisTypeChange = (type: AnalysisType) => {
    setAnalysisType(type);
    // Reset files if analysis type changes to something not requiring them
    if (type !== 'text' && type !== 'text_and_image') setTextFile(null);
    if (type !== 'image' && type !== 'text_and_image') setImageFiles([]);
  };

  const handleTraditionChange = (tradition: string) => {
    setSelectedTraditions(prev => 
      prev.includes(tradition) ? prev.filter(t => t !== tradition) : [...prev, tradition]
    );
  };

  const handleTextFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setTextFile(e.target.files[0]);
    } else {
      setTextFile(null);
    }
  };

  const handleImageFilesChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImageFiles(Array.from(e.target.files));
    } else {
      setImageFiles([]);
    }
  };
  
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => { setIsDragging(false); };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      if (analysisType === 'text' || analysisType === 'text_and_image') {
        // Prioritize text file if multiple dropped, or allow specific drop zones
        const textF = Array.from(e.dataTransfer.files).find(f => f.type.includes('csv') || f.type.includes('excel') || f.type.includes('text'));
        if (textF) setTextFile(textF);
        // Handle image files if relevant
        const imgFs = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (imgFs.length > 0) setImageFiles(prev => [...prev, ...imgFs].slice(0, 5)); // Limit multiple image uploads for now
      } else if (analysisType === 'image') {
        const imgFs = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (imgFs.length > 0) setImageFiles(prev => [...prev, ...imgFs].slice(0, 5));
      }
      e.dataTransfer.clearData();
    }
  }, [analysisType]);

  const handleRunAnalysis = async () => {
    if (isLoading) return;

    setIsLoading(true);
    setIsLoadingGlobal(true); // Update global loading state
    setError(null);
    setJobId(null);
    setJobIdGlobal(null);
    setStatusUrl(null);
    setJobStatus(null);
    onAnalysisStart(); // Notify parent

    const formData = new FormData();
    if (!analysisType) {
      setError("Please select an analysis type.");
      setIsLoading(false);
      setIsLoadingGlobal(false);
      onAnalysisError("Analysis type not selected.");
      return;
    }
    formData.append('analysis_type', analysisType);
    formData.append('data_source_type', dataSourceType);
    
    selectedTraditions.forEach(trad => formData.append('selected_traditions', trad));
    formData.append('advanced_options', JSON.stringify(advancedOptions));

    if (dataSourceType === 'upload') {
      if ((analysisType === 'text' || analysisType === 'text_and_image') && textFile) {
        formData.append('text_file', textFile);
      } else if ((analysisType === 'text' || analysisType === 'text_and_image') && !textFile) {
        setError("Text file selected for upload but no file provided.");
        setIsLoading(false);
        setIsLoadingGlobal(false);
        onAnalysisError("Text file not provided for upload.");
        return;
      }

      if ((analysisType === 'image' || analysisType === 'text_and_image') && imageFiles.length > 0) {
        imageFiles.forEach(file => formData.append('image_files', file));
      } else if ((analysisType === 'image' || analysisType === 'text_and_image') && imageFiles.length === 0) {
        setError("Image analysis selected for upload but no image files provided.");
        setIsLoading(false);
        setIsLoadingGlobal(false);
        onAnalysisError("Image files not provided for upload.");
        return;
      }
    } else if (dataSourceType === 'sample') {
      // TODO: Implement sample data selection and corresponding IDs
      // For now, let's assume some hardcoded IDs if sample is chosen
      if (analysisType === 'text' || analysisType === 'text_and_image') {
        formData.append('sample_text_id', 'sample_text_1'); // Example
      }
      if (analysisType === 'image' || analysisType === 'text_and_image') {
        // formData.append('sample_image_id', 'sample_image_set_1'); // Example
        setError("Sample image analysis not fully implemented in frontend yet.");
        setIsLoading(false);
        setIsLoadingGlobal(false);
        onAnalysisError("Sample image analysis not fully implemented.");
        return;
      }
    }

    console.log("Submitting analysis with formData:", Object.fromEntries(formData.entries()));

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 202 && response.data.job_id && response.data.status_url) {
        setJobId(response.data.job_id);
        setJobIdGlobal(response.data.job_id); // Update global job ID
        setStatusUrl(response.data.status_url);
        setJobStatus(response.data.status || 'pending');
        // Start polling will be handled by App.tsx or context via prop useEffect on jobIdGlobal
      } else {
        throw new Error(response.data.error || 'Failed to submit analysis job.');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || 'An unknown error occurred.';
      setError(errorMsg);
      onAnalysisError(errorMsg);
      setIsLoading(false);
      setIsLoadingGlobal(false);
    }
    // isLoading and setIsLoadingGlobal will be set to false by App.tsx after polling finishes or if initial submission fails and polling doesn't start.
  };
  
  const clearLocalError = () => {
    setError(null);
    // If App.tsx's error state should also be cleared when user interacts with ConfigPanel,
    // a prop function like `clearGlobalError` would be needed from App.tsx.
    // For now, this only clears local ConfigPanel error.
  };

  // Example of clearing error on input change
  const handleDataSourceChange = (source: DataSourceType) => {
    clearLocalError(); // Clear error when user changes data source
    setDataSourceType(source);
    // Reset files if switching away from 'upload'
    if (source !== 'upload') {
        setTextFile(null);
        setImageFiles([]);
    }
  };

  const handleAnalysisTypeChangeWithClear = (type: AnalysisType) => {
    clearLocalError();
    handleAnalysisTypeChange(type);
  }

  const handleTextFileChangeWithClear = (e: ChangeEvent<HTMLInputElement>) => {
    clearLocalError();
    handleTextFileChange(e);
  }

  const handleImageFilesChangeWithClear = (e: ChangeEvent<HTMLInputElement>) => {
    clearLocalError();
    handleImageFilesChange(e);
  }


  return (
    <div 
      className={`${isOpen ? 'w-80' : 'w-0'} transition-all duration-500 overflow-hidden bg-white border-r border-gray-200 shadow-lg relative`}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-transparent to-purple-50/50 pointer-events-none"></div>
      <div className="p-6 relative h-full overflow-y-auto"> {/* Added h-full and overflow-y-auto */}
        <div className="space-y-6"> {/* Reduced space-y for compactness */}
          
          {/* Local Error Display for ConfigPanel specific issues (e.g. initial submission validation) */}
          {error && (
            <div className="p-3 bg-red-100 text-red-700 border border-red-300 rounded-md text-xs flex items-center gap-2">
              <AlertCircle size={14}/> 
              <div>
                <span className="font-semibold">Configuration Error:</span> {error}
              </div>
            </div>
          )}

          {/* Analysis Type */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Wand2 size={14} className="text-blue-500" />
              Analysis Type
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {(['text', 'image'] as AnalysisType[]).map(type => (
                <button
                  key={type}
                  onClick={() => handleAnalysisTypeChangeWithClear(type)}
                  className={`group relative flex flex-col items-center p-3 border-2 rounded-xl transition-all duration-300 hover:shadow-lg hover:scale-[1.03] ${
                    analysisType === type ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200'
                  }`}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br rounded-xl transform scale-0 group-hover:scale-100 transition-transform duration-300 ${
                    analysisType === type ? (type === 'text' ? 'from-blue-100 to-blue-50' : 'from-green-100 to-green-50') : 
                                           (type === 'text' ? 'from-gray-50 to-white' : 'from-gray-50 to-white')
                  }`}></div>
                  {type === 'text' ? <FileText className={`relative mb-1 transform transition-transform group-hover:scale-110 ${analysisType === type ? 'text-blue-500' : 'text-gray-400'}`} /> : <ImageIcon className={`relative mb-1 transform transition-transform group-hover:scale-110 ${analysisType === type ? 'text-green-500' : 'text-gray-400'}`} />}
                  <span className={`relative text-xs font-medium ${analysisType === type ? (type === 'text' ? 'text-blue-700' : 'text-green-700') : 'text-gray-600'}`}>
                    {type?.charAt(0).toUpperCase() + type!.slice(1)}
                  </span>
                </button>
              ))}
            </div>
             {/* Simple toggle for text_and_image if one is already selected */}
            { (analysisType === 'text' || analysisType === 'image') && (
                 <button 
                    onClick={() => handleAnalysisTypeChangeWithClear('text_and_image')}
                    className={`mt-2 w-full text-xs p-2 rounded-md border ${analysisType === 'text_and_image' ? 'bg-purple-100 border-purple-400 text-purple-700' : 'bg-gray-50 hover:bg-gray-100 border-gray-300'}`}
                 >
                    {analysisType === 'text_and_image' ? '✓ Both Text & Image' : 'Analyze Text & Image Together?'}
                 </button>
            )}
            {analysisType === 'text_and_image' && (
                 <button 
                    onClick={() => handleAnalysisTypeChangeWithClear('text')} // Default back to text or based on previous single selection
                    className="mt-2 w-full text-xs p-2 rounded-md bg-purple-100 border-purple-400 text-purple-700"
                 >
                    ✓ Analyzing Text & Image
                 </button>
            )}
          </div>

          {/* Data Input Source */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Upload size={14} className="text-blue-500" />
              Data Source
            </h2>
            <div className="space-y-2">
              {(['upload', 'sample'] as DataSourceType[]).map(source => (
                <button
                  key={source}
                  onClick={() => handleDataSourceChange(source)}
                  className={`w-full p-3 rounded-xl border-2 text-left transition-all duration-300 ${
                    dataSourceType === source
                      ? 'border-blue-500 bg-blue-50 shadow-lg transform scale-[1.02]'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className={`text-sm font-medium ${dataSourceType === source ? 'text-blue-700' : 'text-gray-700'}`}>
                        {source === 'upload' ? 'Upload Your Data' : 'Use Sample Data'}
                      </h3>
                    </div>
                    {source === 'upload' ? <Upload size={16} className={`${dataSourceType === source ? 'text-blue-500' : 'text-gray-400'}`} /> : <FileText size={16} className={`${dataSourceType === source ? 'text-blue-500' : 'text-gray-400'}`} />}
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* File Upload Section (conditional) */}
          {dataSourceType === 'upload' && analysisType && (
            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`mt-4 border-2 border-dashed rounded-xl p-4 text-center transition-all duration-300 ${
                isDragging 
                  ? 'border-blue-500 bg-blue-50 scale-[1.02] shadow-lg' 
                  : 'border-gray-300 hover:border-blue-300 hover:bg-blue-50'
              }`}
            >
              <Upload className={`mx-auto mb-2 transition-all duration-300 ${isDragging ? 'text-blue-500 animate-bounce' : 'text-gray-400 hover:text-blue-500'}`} />
              <p className="text-xs text-gray-600">
                Drag & drop or{' '}
                <label htmlFor="file-upload-input" className="text-blue-500 hover:text-blue-600 font-medium underline decoration-dotted underline-offset-2 cursor-pointer">
                  browse files
                </label>
              </p>
              <input id="file-upload-input" type="file" className="hidden" 
                multiple={(analysisType === 'image' || analysisType === 'text_and_image')}
                accept={
                  analysisType === 'text' ? ".csv,.xlsx,.xls,.txt,.json" : 
                  analysisType === 'image' ? ".jpg,.jpeg,.png,.gif,.webp" : 
                  ".csv,.xlsx,.xls,.txt,.json,.jpg,.jpeg,.png,.gif,.webp" // For text_and_image
                }
                onChange={
                  (analysisType === 'text' && dataSourceType === 'upload') ? handleTextFileChangeWithClear : 
                  ((analysisType === 'image' || analysisType === 'text_and_image') && dataSourceType === 'upload') ? handleImageFilesChangeWithClear : undefined
                } 
              />
              {isDragging && <div className="absolute inset-0 bg-blue-500/5 rounded-xl pointer-events-none"></div>}
              
              {/* Display selected file names */}
              {textFile && (analysisType === 'text' || analysisType === 'text_and_image') && (
                <div className="mt-2 text-xs text-gray-700">
                  <span className="font-semibold text-blue-600">Text File:</span> {textFile.name} ({ (textFile.size / 1024).toFixed(2) } KB)
                </div>
              )}
              {imageFiles.length > 0 && (analysisType === 'image' || analysisType === 'text_and_image') && (
                <div className="mt-2 text-xs text-gray-700">
                  <span className="font-semibold text-green-600">Image File(s):</span>
                  <ul className="list-disc list-inside">
                    {imageFiles.map(f => <li key={f.name}>{f.name.substring(0,25)}... ({(f.size / 1024).toFixed(2)} KB)</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Traditions (simplified multi-select) */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Settings size={14} className="text-blue-500" /> Traditions
            </h2>
            <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_TRADITIONS.map(trad => (
                    <button 
                        key={trad} 
                        onClick={() => { clearLocalError(); handleTraditionChange(trad); }}
                        className={`p-2 text-xs rounded-md border-2 transition-colors ${selectedTraditions.includes(trad) ? 'bg-blue-100 border-blue-400 text-blue-700 font-semibold' : 'bg-gray-50 hover:bg-gray-100 border-gray-300'}`}
                    >
                        {selectedTraditions.includes(trad) ? '✓ ' : ''}{trad.charAt(0).toUpperCase() + trad.slice(1)}
                    </button>
                ))}
            </div>
          </div>

          {/* Advanced Options Placeholder (can be expanded later) */}
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Beaker size={14} className="text-blue-500" />
              Advanced Options
            </h2>
             <button
                onClick={() => setExpandedOption(expandedOption === 'adv_processing' ? null : 'adv_processing')}
                className="w-full p-3 text-left transition-all duration-300 hover:bg-blue-50 focus:outline-none group border-2 border-gray-200 rounded-xl hover:border-blue-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Settings size={14} className="text-gray-400 group-hover:text-blue-500 transition-colors duration-300" />
                    <span className="text-xs font-medium text-gray-700 group-hover:text-blue-600 transition-colors duration-300">Analysis Parameters</span>
                  </div>
                  <ChevronDown
                    size={14}
                    className={`text-gray-400 transform transition-transform duration-300 group-hover:text-blue-500 ${
                      expandedOption === 'adv_processing' ? 'rotate-180' : ''
                    }`}
                  />
                </div>
              </button>
              {expandedOption === 'adv_processing' && (
                <div className="p-3 mt-2 border rounded-lg bg-gray-50 text-xs">
                  <p>Max Tokens (Text): {JSON.stringify(advancedOptions.text_advanced_options?.max_tokens)}</p>
                  <p>Image Feature Level: {JSON.stringify(advancedOptions.image_advanced_options?.feature_level)}</p>
                  {/* TODO: Add inputs to change these options */}
                </div>
              )}
          </div>

          {/* Run Button */}
          <button 
            onClick={handleRunAnalysis}
            disabled={isLoading || !analysisType || dataSourceType === 'none' || (dataSourceType === 'upload' && analysisType === 'text' && !textFile) || (dataSourceType === 'upload' && analysisType === 'image' && imageFiles.length === 0) || (dataSourceType === 'upload' && analysisType === 'text_and_image' && (!textFile || imageFiles.length === 0)) }
            className="relative w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 rounded-xl font-medium transition-all duration-300 hover:shadow-xl hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>
            <div className="relative flex items-center justify-center gap-2">
              {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} className="transform group-hover:rotate-12 transition-transform duration-300" />}
              <span>{isLoading ? (jobStatus || 'Analyzing...') : 'Run Analysis'}</span>
            </div>
          </button>

          {/* Status/Error Display */}
          {error && <div className="mt-3 p-3 bg-red-50 text-red-700 border border-red-200 rounded-md text-xs flex items-center gap-2"><AlertCircle size={14}/> {error}</div>}
          {jobId && !error && <div className="mt-3 p-3 bg-green-50 text-green-700 border border-green-200 rounded-md text-xs flex items-center gap-2"><CheckCircle size={14}/> Job Submitted: {jobId.substring(0,8)}...</div>}
          {jobStatus && <div className="mt-1 p-2 bg-blue-50 text-blue-700 border border-blue-200 rounded-md text-xs">Status: {jobStatus}</div>}

        </div>
      </div>
    </div>
  );
}

export default ConfigPanel;