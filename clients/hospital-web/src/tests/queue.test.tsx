import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueueMetrics } from '../components/queue/QueueMetrics';
import { QueueTable } from '../components/queue/QueueTable';
import { Consultation } from '../types/consultation';

describe('OPD Queue Components', () => {
  it('renders queue metrics with correct values', () => {
    render(
      <QueueMetrics
        waitingCount={8}
        inConsultationCount={4}
        completedCount={12}
        urgentCount={2}
      />
    );

    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Patients Waiting')).toBeInTheDocument();
    expect(screen.getByText('In Consultation')).toBeInTheDocument();
  });

  it('renders queue table with patient tokens and handles row selection', () => {
    const mockConsultations: Consultation[] = [
      {
        id: 'c-101-uuid',
        patient_id: 'p-201-uuid',
        hospital_id: 'h-1-uuid',
        status: 'initiated',
        chief_complaint: 'Persistent dry cough and fever for 4 days',
        started_at: null,
        completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 'c-102-uuid',
        patient_id: 'p-202-uuid',
        hospital_id: 'h-1-uuid',
        status: 'completed',
        chief_complaint: 'Routine BP follow-up',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const onSelect = vi.fn();

    render(
      <BrowserRouter>
        <QueueTable
          consultations={mockConsultations}
          onSelectConsultation={onSelect}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('#2')).toBeInTheDocument();
    expect(screen.getByText(/Patient #p-201-u/i)).toBeInTheDocument();
    expect(screen.getByText(/Persistent dry cough and fever for 4 days/i)).toBeInTheDocument();

    const openBtns = screen.getAllByRole('button', { name: /Open Case/i });
    expect(openBtns.length).toBe(2);

    fireEvent.click(openBtns[0]);
    expect(onSelect).toHaveBeenCalledWith(mockConsultations[0]);
  });
});
