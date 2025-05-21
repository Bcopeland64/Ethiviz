import React from 'react';
import WelcomeMessage from './WelcomeMessage';

interface MainContentProps {
  sidebarOpen: boolean;
}

function MainContent({ sidebarOpen }: MainContentProps) {
  return (
    <main className={`flex-1 p-6 transition-all duration-300 ${sidebarOpen ? 'ml-0' : 'ml-0'}`}>
      <WelcomeMessage />
    </main>
  );
}

export default MainContent;