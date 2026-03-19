import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/home/Home'
import React, { useContext, useState } from 'react';

type AppContextType = {
  selectedMatchField: string;
  setSelectedMatchField: (v: string) => void;
  selectedUser: string;
  setSelectedUser: (u: string) => void;
  selectedReRanker: string;
  setSelectedReRanker: (r: string) => void;
  selectedCompletion: string;
  setSelectedCompletion: (c: string) => void;
};

export const UserContext = React.createContext<AppContextType | undefined>(undefined);

const App = () => {
  const [selectedMatchField, setSelectedMatchField] = useState("vector1");
  const [selectedReRanker, setSelectedReRanker] = useState("voyage/rerank-2");
  const [selectedUser, setSelectedUser] = useState("1");
  const [selectedCompletion, setSelectedCompletion] = useState("us.amazon.nova-lite-v1:0");

  return (
    <Router>
      <UserContext.Provider value={{
        selectedMatchField, setSelectedMatchField,
        selectedUser, setSelectedUser,
        selectedReRanker, setSelectedReRanker,
        selectedCompletion, setSelectedCompletion
      }}>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </UserContext.Provider>
    </Router>
  )
}

export function useUserContext() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUserContext must be used within UserProvider");
  }
  return context;
}

export default App
