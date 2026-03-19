import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { UserContext } from '../../App';
import Menu from './Menu';

const defaultContext = {
  selectedMatchField: 'vector1',
  setSelectedMatchField: jest.fn(),
  selectedUser: '1',
  setSelectedUser: jest.fn(),
  selectedReRanker: 'voyage/rerank-2',
  setSelectedReRanker: jest.fn(),
  selectedCompletion: 'us.amazon.nova-lite-v1:0',
  setSelectedCompletion: jest.fn(),
};

const renderMenu = (overrides = {}) => {
  const ctx = { ...defaultContext, ...overrides };
  return render(
    <UserContext.Provider value={ctx}>
      <Menu />
    </UserContext.Provider>
  );
};

describe('Menu', () => {
  test('renders two dropdown labels', () => {
    renderMenu();
    expect(screen.getByText('Reranker')).toBeInTheDocument();
    expect(screen.getByText('Completion')).toBeInTheDocument();
  });

  test('renders two select elements', () => {
    renderMenu();
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBe(2);
  });

  test('reranker dropdown has correct options', () => {
    renderMenu();
    expect(screen.getByText('Voyage AI Rerank')).toBeInTheDocument();
    expect(screen.getByText('No Reranking')).toBeInTheDocument();
  });

  test('completion dropdown has correct options', () => {
    renderMenu();
    expect(screen.getByText('Nova Lite')).toBeInTheDocument();
    expect(screen.getByText('Nova Pro')).toBeInTheDocument();
    expect(screen.getByText('Claude Sonnet 4')).toBeInTheDocument();
  });

  test('changing reranker calls setSelectedReRanker', () => {
    const setSelectedReRanker = jest.fn();
    renderMenu({ setSelectedReRanker });

    const rerankerSelect = screen.getByLabelText('Select reranker');
    fireEvent.change(rerankerSelect, { target: { value: 'no-rerank' } });
    expect(setSelectedReRanker).toHaveBeenCalledWith('No rerank');
  });

  test('changing completion calls setSelectedCompletion', () => {
    const setSelectedCompletion = jest.fn();
    renderMenu({ setSelectedCompletion });

    const completionSelect = screen.getByLabelText('Select completion model');
    fireEvent.change(completionSelect, { target: { value: 'nova-pro' } });
    expect(setSelectedCompletion).toHaveBeenCalledWith('us.amazon.nova-pro-v1:0');
  });

  test('selecting "Custom..." shows text input for reranker', () => {
    renderMenu();
    const rerankerSelect = screen.getByLabelText('Select reranker');
    fireEvent.change(rerankerSelect, { target: { value: 'custom' } });

    expect(screen.getByPlaceholderText('provider/model')).toBeInTheDocument();
  });

  test('selecting "Custom..." shows text input for completion', () => {
    renderMenu();
    const completionSelect = screen.getByLabelText('Select completion model');
    fireEvent.change(completionSelect, { target: { value: 'custom' } });

    expect(screen.getByPlaceholderText('provider/model (e.g., openai/gpt-4)')).toBeInTheDocument();
  });

  test('custom reranker value unknown shows custom option selected', () => {
    renderMenu({ selectedReRanker: 'my-custom/reranker' });
    const rerankerSelect = screen.getByLabelText('Select reranker');
    expect((rerankerSelect as HTMLSelectElement).value).toBe('custom');
  });
});
