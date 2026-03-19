import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from './Header';

const renderHeader = () => {
  return render(
    <BrowserRouter>
      <Header />
    </BrowserRouter>
  );
};

describe('Header', () => {
  test('renders the logo image', () => {
    renderHeader();
    const logo = screen.getByAltText('Logo');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveClass('logo-image');
  });

  test('renders "Powered by" label', () => {
    renderHeader();
    expect(screen.getByText('Powered by')).toBeInTheDocument();
  });

  test('renders AWS badge', () => {
    renderHeader();
    const badge = screen.getByText('AWS');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-aws');
  });

  test('renders MongoDB Atlas badge', () => {
    renderHeader();
    const badge = screen.getByText('MongoDB Atlas');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-mongodb');
  });

  test('renders Voyage AI badge', () => {
    renderHeader();
    const badge = screen.getByText('Voyage AI');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge', 'badge-voyage');
  });

  test('logo has cursor pointer style', () => {
    renderHeader();
    const logo = screen.getByAltText('Logo');
    expect(logo).toHaveStyle({ cursor: 'pointer' });
  });
});
