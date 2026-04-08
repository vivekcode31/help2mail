import React, { useState, useRef, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, FileText } from 'lucide-react';
import { api } from '../api';
import { Card, CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import { Input, TextArea } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export function Dashboard() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const excelInputRef = useRef<HTMLInputElement>(null);
  const resumeInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!excelFile || !resumeFile || !subject || !description) {
      setError('Please fill in all fields and select both files.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('excel_file', excelFile);
      formData.append('resume', resumeFile);
      formData.append('subject', subject);
      formData.append('description', description);

      const res = await api.post('/campaign/start', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (res.data.campaign_id) {
        navigate(`/campaign/${res.data.campaign_id}`);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.response?.data?.error || 'An error occurred while starting the campaign.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Card>
        <CardHeader 
          title="Create New Campaign" 
          description="Upload your contact list and resume to queue a new bulk-send job." 
        />
        <form onSubmit={handleSubmit}>
          <CardContent>
            {error && <div className="mb-4 text-sm text-error bg-red-50 p-3 rounded-md border border-red-100">{error}</div>}
            
            <div className="flex gap-4 mb-4">
              <div 
                className="flex flex-col items-center justify-center p-6 border border-dashed rounded-md w-full cursor-pointer hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--color-border)' }}
                onClick={() => excelInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  ref={excelInputRef} 
                  onChange={(e) => setExcelFile(e.target.files?.[0] || null)} 
                  accept=".csv,.xlsx" 
                  className="hidden" 
                  style={{ display: 'none' }}
                />
                <FileSpreadsheet size={32} className="mb-2 text-light" />
                <span className="text-sm font-medium">{excelFile ? excelFile.name : 'Upload Contacts (.csv, .xlsx)'}</span>
              </div>

              <div 
                className="flex flex-col items-center justify-center p-6 border border-dashed rounded-md w-full cursor-pointer hover:bg-gray-50 transition-colors"
                style={{ borderColor: 'var(--color-border)' }}
                onClick={() => resumeInputRef.current?.click()}
              >
                <input 
                  type="file" 
                  ref={resumeInputRef} 
                  onChange={(e) => setResumeFile(e.target.files?.[0] || null)} 
                  accept="application/pdf" 
                  className="hidden" 
                  style={{ display: 'none' }}
                />
                <FileText size={32} className="mb-2 text-light" />
                <span className="text-sm font-medium">{resumeFile ? resumeFile.name : 'Upload Resume (.pdf)'}</span>
              </div>
            </div>

            <Input 
              label="Email Subject" 
              placeholder="Application for Software Engineer Role" 
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              maxLength={200}
            />

            <TextArea 
              label="Application Description (Body)" 
              placeholder="I am writing to express my interest in..." 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              maxLength={2000}
            />

          </CardContent>
          <CardFooter className="flex justify-end">
            <Button type="submit" isLoading={isLoading}>
              <Upload size={16} style={{marginRight: '8px'}}/> Start Campaign
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
