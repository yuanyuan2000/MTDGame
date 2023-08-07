import React, { useEffect, useRef } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

const Terminal = ({ command }) => {
  const terminalRef = useRef(null);
  const xtermRef = useRef(null);
  const fitAddon = useRef(new FitAddon());

  useEffect(() => {
    xtermRef.current = new XTerm();
    xtermRef.current.loadAddon(fitAddon.current);

    xtermRef.current.open(terminalRef.current);
    xtermRef.current.writeln('Hi defender, welcome to MTD game!');
    xtermRef.current.writeln('A host will turn red when it has been compromised by attcker.');
    xtermRef.current.writeln('Your job is to protect the main database(white node) for 5 minutes. Apply some MTD operation to protect it now!');

    const handleResize = () => {
      fitAddon.current.fit();
    };

    handleResize(); // Fit the terminal initially
    window.addEventListener('resize', handleResize); // Fit the terminal on window resize

    return () => {
      xtermRef.current.dispose();
      window.removeEventListener('resize', handleResize); // Clean up the event listener
    };
  }, []);

  useEffect(() => {
    if (xtermRef.current && command) {
      xtermRef.current.writeln(command);
    }
  }, [command]);

  return (
    <div
      ref={terminalRef}
      style={{
        width: '100%', // Set the desired width
        height: '100%', // Set the desired height
      }}
    />
  );
};

export default Terminal;

