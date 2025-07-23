import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronUp, ChevronDown } from 'lucide-react';

interface DateTimePickerProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const DateTimePicker: React.FC<DateTimePickerProps> = ({ value, onChange, placeholder = "Select date and time" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(value ? new Date(value) : null);
  const [selectedHour, setSelectedHour] = useState(value ? new Date(value).getHours() : 0);
  const [selectedMinute, setSelectedMinute] = useState(value ? new Date(value).getMinutes() : 0);

  // Generate calendar days
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDay; i++) {
      days.push(null);
    }
    
    // Add days of the month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    
    return days;
  };

  const days = getDaysInMonth(currentDate);
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    updateDateTime(date, selectedHour, selectedMinute);
  };

  const handleHourSelect = (hour: number) => {
    setSelectedHour(hour);
    if (selectedDate) {
      updateDateTime(selectedDate, hour, selectedMinute);
    }
  };

  const handleMinuteSelect = (minute: number) => {
    setSelectedMinute(minute);
    if (selectedDate) {
      updateDateTime(selectedDate, selectedHour, minute);
    }
  };

  const updateDateTime = (date: Date, hour: number, minute: number) => {
    const newDateTime = new Date(date);
    newDateTime.setHours(hour, minute, 0, 0);
    onChange(newDateTime.toISOString().slice(0, 16));
  };

  const formatDisplayValue = () => {
    if (!value) return placeholder;
    const date = new Date(value);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isSelected = (date: Date) => {
    if (!selectedDate) return false;
    return date.toDateString() === selectedDate.toDateString();
  };

  const isPastDate = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  };

  const formatTime12Hour = (hour: number, minute: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
  };

  return (
    <div className="relative">
      {/* Input Field */}
      <input
        type="text"
        value={formatDisplayValue()}
        onClick={() => setIsOpen(!isOpen)}
        readOnly
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer bg-white"
        placeholder={placeholder}
      />

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-xl border border-gray-200 p-6 z-50 min-w-[600px]">
          <div className="grid grid-cols-2 gap-6">
            {/* Calendar Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <button
                  onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <h3 className="text-lg font-semibold text-gray-900">
                  {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                </h3>
                <button
                  onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-1">
                {/* Day headers */}
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                  <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                    {day}
                  </div>
                ))}
                
                {/* Calendar days */}
                {days.map((date, index) => (
                  <div key={index} className="text-center">
                    {date ? (
                      <button
                        onClick={() => handleDateSelect(date)}
                        disabled={isPastDate(date)}
                        className={`
                          w-8 h-8 rounded-lg text-sm font-medium transition-colors
                          ${isSelected(date) 
                            ? 'bg-primary-600 text-white' 
                            : isToday(date)
                            ? 'bg-primary-100 text-primary-800'
                            : isPastDate(date)
                            ? 'text-gray-300 cursor-not-allowed'
                            : 'text-gray-700 hover:bg-gray-100'
                          }
                        `}
                      >
                        {date.getDate()}
                      </button>
                    ) : (
                      <div className="w-8 h-8" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Time Selection Section */}
            <div className="space-y-4">
              {/* Time Display */}
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {formatTime12Hour(selectedHour, selectedMinute)}
                </div>
                <div className="text-sm text-gray-500">
                  {selectedDate ? selectedDate.toLocaleDateString() : 'Select a date'}
                </div>
              </div>

              {/* Quick Time Presets */}
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-3">Quick Select</h4>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: 'Now', hour: new Date().getHours(), minute: Math.ceil(new Date().getMinutes() / 15) * 15 },
                    { label: '5 min', hour: new Date().getHours(), minute: Math.ceil((new Date().getMinutes() + 5) / 15) * 15 },
                    { label: '15 min', hour: new Date().getHours(), minute: Math.ceil((new Date().getMinutes() + 15) / 15) * 15 }
                  ].map((preset, index) => {
                    const adjustedHour = preset.minute >= 60 ? preset.hour + 1 : preset.hour;
                    const adjustedMinute = preset.minute >= 60 ? preset.minute - 60 : preset.minute;
                    return (
                      <button
                        key={index}
                        onClick={() => {
                          handleHourSelect(adjustedHour);
                          handleMinuteSelect(adjustedMinute);
                        }}
                        className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        {preset.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Time Input */}
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Time</label>
                  <div className="flex gap-2">
                    {/* Hour Dropdown */}
                    <select
                      value={selectedHour}
                      onChange={(e) => handleHourSelect(parseInt(e.target.value))}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      {Array.from({ length: 24 }, (_, i) => (
                        <option key={i} value={i}>
                          {formatTime12Hour(i, 0).replace(':00', '')}
                        </option>
                      ))}
                    </select>

                    {/* Minute Dropdown */}
                    <select
                      value={selectedMinute}
                      onChange={(e) => handleMinuteSelect(parseInt(e.target.value))}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    >
                      {[0, 15, 30, 45].map(minute => (
                        <option key={minute} value={minute}>
                          {minute.toString().padStart(2, '0')}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Confirm
            </button>
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default DateTimePicker; 