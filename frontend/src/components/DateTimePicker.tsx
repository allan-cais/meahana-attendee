import React, { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';

interface DateTimePickerProps {
  value?: string;
  onChange: (value: string | undefined) => void;
  placeholder?: string;
}

const DateTimePicker: React.FC<DateTimePickerProps> = ({
  value,
  onChange,
  placeholder = "Select date and time"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localValue, setLocalValue] = useState(value || '');

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setLocalValue(date);
    
    if (date) {
      // Convert to ISO string for consistency
      const dateObj = new Date(date);
      onChange(dateObj.toISOString());
    } else {
      onChange(undefined);
    }
  };

  const handleClear = () => {
    setLocalValue('');
    onChange(undefined);
    setIsOpen(false);
  };

  const formatDisplayValue = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="datetime-local"
          value={localValue}
          onChange={handleDateChange}
          className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder={placeholder}
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Calendar className="h-5 w-5 text-gray-400" />
        </div>
      </div>
      
      {/* Clear button */}
      {localValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </button>
      )}
      
      {/* Display value */}
      {value && (
        <div className="mt-2 text-sm text-gray-600 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          <span>Will join at: {formatDisplayValue(value)}</span>
        </div>
      )}
    </div>
  );
};

export default DateTimePicker; 