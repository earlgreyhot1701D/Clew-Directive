'use client';

import { useState, useEffect } from 'react';
import { submitVibeCheck, refineProfile, generateBriefing, ClewApiError, type LearningResource } from '@/lib/api';

/**
 * Clew Directive — Main Page
 *
 * Three-phase architecture:
 *   1. boot     — System initialization sequence
 *   2. landing  — Privacy notice + start button
 *   3. working  — Single scrolling page with progressive sections:
 *                 - Calibration (all 4 questions)
 *                 - Profile Synthesis (appears after generation)
 *                 - Processing (appears during briefing generation)
 *                 - Command Briefing (appears when complete)
 */

type AppPhase = 'landing' | 'working';

export default function Home() {
  const [appPhase, setAppPhase] = useState<AppPhase>('landing');
  const [showPrivacyNotice, setShowPrivacyNotice] = useState(true);
  const [showAboutModal, setShowAboutModal] = useState(false);
  
  // Working interface state
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [vibeCheckResponses, setVibeCheckResponses] = useState<Record<string, string>>({});
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);
  const [profile, setProfile] = useState<string | null>(null);
  const [showRefinement, setShowRefinement] = useState(false);
  const [userCorrection, setUserCorrection] = useState('');
  const [isGeneratingProfile, setIsGeneratingProfile] = useState(false);
  const [isGeneratingBriefing, setIsGeneratingBriefing] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [briefing, setBriefing] = useState<any>(null);
  
  // Error handling state
  const [error, setError] = useState<string | null>(null);
  const [retryAllowed, setRetryAllowed] = useState(true);
  const [retryAction, setRetryAction] = useState<(() => void) | null>(null);

  // Calibration questions
  const questions = [
    {
      id: 'skepticism',
      number: 1,
      label: 'AI Experience',
      question: 'Which best describes your current take on AI?',
      options: [
        "Skeptical — I want to understand what's real",
        "Curious but haven't started learning",
        "I've dabbled and want more structure",
        "I use AI tools already and want to go deeper"
      ]
    },
    {
      id: 'goal',
      number: 2,
      label: 'Primary Goal',
      question: 'If AI could help you with one thing, what would it be?',
      options: [
        "Understand what AI actually is and isn't",
        "Use AI tools to be better at my current job",
        "Build things with AI",
        "Make career decisions about AI"
      ]
    },
    {
      id: 'learning_style',
      number: 3,
      label: 'Learning Style',
      question: 'How do you prefer to learn new things?',
      options: [
        "Reading and thinking at my own pace",
        "Watching videos with examples",
        "Hands-on projects and exercises",
        "Structured courses with a clear path"
      ]
    },
    {
      id: 'context',
      number: 4,
      label: 'Background',
      question: "What best describes your current situation?",
      options: [
        "Student or Academic",
        "Business / Marketing / Operations",
        "Technical / Engineering / IT",
        "Creative / Design / Media",
        "Healthcare / Legal / Public Service",
        "Career Transition / Exploring AI"
      ]
    }
  ];

  // Handler functions
  const handleAnswerQuestion = (questionId: string, answer: string) => {
    setVibeCheckResponses(prev => ({ ...prev, [questionId]: answer }));
    
    // Auto-advance to next question
    const currentIdx = questions.findIndex(q => q.id === questionId);
    if (currentIdx < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestion(currentIdx + 1);
        // Scroll to next question
        document.getElementById(`question-${currentIdx + 1}`)?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }, 300);
    }
  };

  const handleEditQuestion = (questionIndex: number) => {
    setEditingQuestion(questionIndex);
    setCurrentQuestion(questionIndex);
  };

  const handleGenerateProfile = async () => {
    setIsGeneratingProfile(true);
    setError(null);
    
    try {
      const response = await submitVibeCheck(vibeCheckResponses);
      setProfile(response.profile);
      
      // Scroll to profile section
      setTimeout(() => {
        document.getElementById('profile')?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    } catch (err) {
      if (err instanceof ClewApiError) {
        setError(err.message);
        setRetryAllowed(err.retryAllowed);
        setRetryAction(() => handleGenerateProfile);
      } else {
        setError('An unexpected error occurred. Please try again.');
        setRetryAllowed(true);
        setRetryAction(() => handleGenerateProfile);
      }
      console.error('Profile generation failed:', err);
    } finally {
      setIsGeneratingProfile(false);
    }
  };

  const handleApproveProfile = async () => {
    if (!profile) return;
    
    setIsGeneratingBriefing(true);
    setLoadingStep(0);
    setError(null);
    
    // Progressive loading messages
    const loadingSteps = [
      { delay: 0, step: 0 },
      { delay: 2000, step: 1 },
      { delay: 5000, step: 2 },
      { delay: 10000, step: 3 },
    ];
    
    // Set up progressive loading
    const timers = loadingSteps.map(({ delay, step }) =>
      setTimeout(() => setLoadingStep(step), delay)
    );
    
    // Scroll to loading section
    setTimeout(() => {
      document.getElementById('loading')?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }, 100);

    try {
      const response = await generateBriefing(profile);
      
      // Clear all timers
      timers.forEach(timer => clearTimeout(timer));
      
      setBriefing(response);
      
      // Scroll to briefing section
      setTimeout(() => {
        document.getElementById('briefing')?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    } catch (err) {
      // Clear all timers
      timers.forEach(timer => clearTimeout(timer));
      
      if (err instanceof ClewApiError) {
        setError(err.message);
        setRetryAllowed(err.retryAllowed);
        setRetryAction(() => handleApproveProfile);
      } else {
        setError('An unexpected error occurred. Please try again.');
        setRetryAllowed(true);
        setRetryAction(() => handleApproveProfile);
      }
      console.error('Briefing generation failed:', err);
    } finally {
      setIsGeneratingBriefing(false);
    }
  };

  const handleRefineProfile = async () => {
    if (!profile || !userCorrection.trim()) return;
    
    setIsGeneratingProfile(true);
    setError(null);
    setShowRefinement(false);
    
    try {
      const response = await refineProfile(profile, userCorrection);
      setProfile(response.profile);
      setUserCorrection('');
      
      // Scroll to updated profile
      setTimeout(() => {
        document.getElementById('profile')?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    } catch (err) {
      if (err instanceof ClewApiError) {
        setError(err.message);
        setRetryAllowed(err.retryAllowed);
        setRetryAction(() => handleRefineProfile);
      } else {
        setError('An unexpected error occurred. Please try again.');
        setRetryAllowed(true);
        setRetryAction(() => handleRefineProfile);
      }
      console.error('Profile refinement failed:', err);
      setShowRefinement(true); // Keep refinement UI open on error
    } finally {
      setIsGeneratingProfile(false);
    }
  };

  return (
    <main
      role="main"
      aria-label="Clew Directive AI Learning Navigator"
      style={{ 
        minHeight: '100vh',
      }}
    >
      {/* WCAG: Skip link for keyboard navigation */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <div id="main-content">
        {/* PHASE 1: Landing Page - Two Column Layout */}
        {appPhase === 'landing' && (
          <div style={{
            maxWidth: '1100px',
            margin: '0 auto',
            padding: '1.5rem 1rem',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}>
            <section aria-label="Welcome" className="terminal-container" style={{ position: 'relative', padding: '1.5rem 2rem' }}>
              {/* About Button - Top Right */}
              <div style={{ 
                position: 'absolute',
                top: '0.75rem',
                right: '0.75rem'
              }}>
                <button
                  onClick={() => setShowAboutModal(true)}
                  className="ghost-btn"
                  aria-label="Learn more about Clew Directive"
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.7rem' }}
                >
                  About
                </button>
              </div>

              {/* Header Section */}
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <h1 className="terminal-glow" style={{ marginBottom: '0.5rem', fontSize: '2rem' }}>
                  [ CLEW DIRECTIVE ]
                </h1>
                
                <h2 style={{ 
                  fontSize: '1.3rem',
                  fontWeight: 'bold',
                  textTransform: 'none',
                  letterSpacing: '0.02em',
                  marginBottom: '0.25rem'
                }}>
                  Get Your Free AI Learning Plan in 2 Minutes
                </h2>

                <p style={{ 
                  color: 'var(--text-dim)',
                  fontSize: '0.9rem',
                  fontStyle: 'italic'
                }}>
                  Stop following the hype. Start with a path built for you.
                </p>
              </div>

              {/* Two Column Layout */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '2.5rem',
                marginBottom: '1rem',
                alignItems: 'start'
              }} className="landing-columns">
                {/* LEFT COLUMN - Problem & CTA */}
                <div>
                  <p style={{ 
                    color: 'var(--text-primary)',
                    fontSize: '1rem',
                    lineHeight: '1.6',
                    marginBottom: '1.25rem'
                  }}>
                    New to AI? Overwhelmed by where to begin? We'll build a learning path that matches your experience, goals, and learning style — no fluff, just trusted resources.
                  </p>

                  {/* Trust Signals */}
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.4rem',
                    marginBottom: '1.25rem',
                    fontSize: '0.85rem',
                    color: 'var(--text-dim)'
                  }}>
                    <div>✓ No Account Required</div>
                    <div>✓ No Tracking</div>
                    <div>✓ Free to Use</div>
                  </div>

                  {/* Privacy Notice */}
                  {showPrivacyNotice && (
                    <div
                      role="alert"
                      className="terminal-alert terminal-alert-dismissible"
                      style={{ marginBottom: '1rem', fontSize: '0.8rem', padding: '0.75rem', paddingRight: '2.5rem' }}
                    >
                      <button
                        className="terminal-alert-close"
                        onClick={() => setShowPrivacyNotice(false)}
                        aria-label="Dismiss privacy notice"
                        style={{ fontSize: '1.2rem', top: '0.25rem', right: '0.25rem' }}
                      >
                        ×
                      </button>
                      <p style={{ margin: 0, lineHeight: '1.4' }}>
                        <strong>Privacy:</strong> No cookies, no tracking. Your plan is yours to keep.
                      </p>
                    </div>
                  )}

                  {/* CTA Button */}
                  <button
                    onClick={() => setAppPhase('working')}
                    className="terminal-button"
                    aria-label="Start the assessment to get your learning plan"
                    style={{ 
                      fontSize: '0.95rem',
                      padding: '0.85rem 1.75rem',
                      width: '100%'
                    }}
                  >
                    Get My Learning Plan
                  </button>
                </div>

                {/* RIGHT COLUMN - How It Works */}
                <div style={{
                  border: '1px solid var(--border-color)',
                  padding: '1.5rem',
                  background: 'rgba(0, 0, 0, 0.2)',
                  height: '100%'
                }}>
                  <h3 style={{ 
                    fontSize: '0.9rem',
                    marginBottom: '1.25rem',
                    textAlign: 'center',
                    color: 'var(--text-primary)',
                    letterSpacing: '0.1em'
                  }}>
                    HOW IT WORKS
                  </h3>

                  <div style={{ 
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1.25rem'
                  }}>
                    <div>
                      <div style={{ 
                        color: 'var(--text-primary)', 
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        marginBottom: '0.35rem'
                      }}>
                        1. Answer 4 Questions
                        <span style={{ color: 'var(--text-dim)', fontWeight: 'normal' }}> (2 min)</span>
                      </div>
                      <p style={{ 
                        color: 'var(--text-dim)', 
                        fontSize: '0.8rem',
                        lineHeight: '1.5',
                        margin: 0
                      }}>
                        Your experience level, learning goals, preferred style, and background
                      </p>
                    </div>

                    <div>
                      <div style={{ 
                        color: 'var(--text-primary)', 
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        marginBottom: '0.35rem'
                      }}>
                        2. Get Your Profile
                      </div>
                      <p style={{ 
                        color: 'var(--text-dim)', 
                        fontSize: '0.8rem',
                        lineHeight: '1.5',
                        margin: 0
                      }}>
                        We analyze your answers and match you to the right resources
                      </p>
                    </div>

                    <div>
                      <div style={{ 
                        color: 'var(--text-primary)', 
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        marginBottom: '0.35rem'
                      }}>
                        3. Download Curated Plan
                      </div>
                      <p style={{ 
                        color: 'var(--text-dim)', 
                        fontSize: '0.8rem',
                        lineHeight: '1.5',
                        margin: 0
                      }}>
                        4-6 hand-picked resources with explanations
                      </p>
                    </div>
                  </div>

                  <p style={{
                    marginTop: '1.25rem',
                    paddingTop: '1.25rem',
                    borderTop: '1px solid rgba(255, 214, 10, 0.2)',
                    textAlign: 'center',
                    fontSize: '0.75rem',
                    color: 'var(--text-dim)',
                    lineHeight: '1.5',
                    margin: '1.25rem 0 0 0'
                  }}>
                    All resources are free to access. Some may offer paid certificates.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div style={{ 
                marginTop: '1rem', 
                paddingTop: '1rem',
                borderTop: '1px solid var(--border-color)',
                fontSize: '0.65rem',
                color: 'var(--text-dim)',
                textAlign: 'center'
              }}>
                <p style={{ margin: 0 }}>
                  Open Source • Built by{' '}
                  <a 
                    href="https://www.linkedin.com/in/la-shara-cordero-a0017a11/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ color: 'var(--text-primary)', textDecoration: 'underline' }}
                  >
                    La-Shara Cordero
                  </a>
                </p>
              </div>
            </section>
          </div>
        )}

        {/* PHASE 2: Working Interface - Single Scrolling Page */}
        {appPhase === 'working' && (
          <>
            {/* Sticky Header - Always Visible */}
            <div style={{ 
              position: 'sticky',
              top: 0,
              left: 0,
              right: 0,
              zIndex: 100,
              background: 'var(--bg-primary)',
              borderBottom: '1px solid var(--border-color)',
              padding: '1rem 2rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <button
                onClick={() => {
                  if (window.confirm('Start over? This will clear all your answers and reset the assessment.')) {
                    // Reset all state
                    setVibeCheckResponses({});
                    setProfile(null);
                    setBriefing(null);
                    setShowRefinement(false);
                    setUserCorrection('');
                    setCurrentQuestion(0);
                    setEditingQuestion(null);
                    setIsGeneratingProfile(false);
                    setIsGeneratingBriefing(false);
                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
                className="ghost-btn"
                aria-label="Start over and clear all answers"
              >
                Start Over
              </button>

              <button
                onClick={() => setShowAboutModal(true)}
                className="ghost-btn"
                aria-label="Learn more about Clew Directive"
              >
                About
              </button>
            </div>

            {/* Main Content - Scrolls Underneath Sticky Header */}
            <div className="working-interface">
            {/* SECTION 1: CALIBRATION - Accordion Wizard */}
            <section id="calibration" className="terminal-container" aria-label="Quick assessment">
              <h2>━━━ QUICK ASSESSMENT ━━━</h2>
              
              {/* Progress Bar */}
              <div className="progress-container" style={{ marginBottom: '2rem' }}>
                <div className="progress-label">
                  PROGRESS: {Object.keys(vibeCheckResponses).length}/4 COMPLETE
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(Object.keys(vibeCheckResponses).length / 4) * 100}%` }}
                  />
                </div>
              </div>

              {/* Accordion Questions */}
              <div className="question-accordion">
                {questions.map((q, idx) => {
                  const isAnswered = !!vibeCheckResponses[q.id];
                  const isActive = currentQuestion === idx || editingQuestion === idx;
                  const isLocked = idx > 0 && !vibeCheckResponses[questions[idx - 1].id];

                  return (
                    <div 
                      key={q.id} 
                      id={`question-${idx}`}
                      className={`question-item ${isAnswered ? 'answered' : ''} ${isActive ? 'active' : ''} ${isLocked ? 'locked' : ''}`}
                    >
                      {/* Question Header */}
                      <div className="question-header">
                        <div className="question-number">
                          {isAnswered ? '✓' : String(q.number).padStart(2, '0')}
                        </div>
                        <div className="question-title">
                          <div className="question-label">{q.label}</div>
                          {isAnswered && !isActive && (
                            <div className="question-answer-preview">
                              {vibeCheckResponses[q.id]}
                            </div>
                          )}
                        </div>
                        {isAnswered && !isActive && (
                          <button
                            onClick={() => handleEditQuestion(idx)}
                            className="edit-btn"
                            aria-label={`Edit answer for ${q.label}`}
                          >
                            [edit]
                          </button>
                        )}
                        {isLocked && (
                          <div className="locked-indicator" aria-label="Question locked">
                            🔒
                          </div>
                        )}
                      </div>

                      {/* Question Content (Expanded) */}
                      {isActive && !isLocked && (
                        <div className="question-content">
                          <p className="question-text">{q.question}</p>
                          <div className="radio-group">
                            {q.options.map((option, i) => (
                              <label key={i} className="radio-label">
                                <input
                                  type="radio"
                                  name={q.id}
                                  value={option}
                                  checked={vibeCheckResponses[q.id] === option}
                                  onChange={(e) => handleAnswerQuestion(q.id, e.target.value)}
                                />
                                <span className="radio-text">{option}</span>
                              </label>
                            ))}
                          </div>
                          {vibeCheckResponses[q.id] && idx < questions.length - 1 && (
                            <button
                              onClick={() => {
                                setEditingQuestion(null);
                                setCurrentQuestion(idx + 1);
                              }}
                              className="terminal-button"
                              style={{ marginTop: '1rem' }}
                            >
                              Continue
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Generate Profile Button */}
              <button
                onClick={handleGenerateProfile}
                disabled={Object.keys(vibeCheckResponses).length < 4 || isGeneratingProfile}
                className="terminal-button"
                style={{ 
                  width: '100%', 
                  marginTop: '2rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem'
                }}
              >
                {isGeneratingProfile && (
                  <div className="spinner" style={{
                    display: 'inline-block',
                    width: '16px',
                    height: '16px',
                    border: '2px solid rgba(255, 214, 10, 0.3)',
                    borderTopColor: 'var(--accent-primary)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                )}
                {isGeneratingProfile ? 'Creating Your Profile...' : 'See My Plan'}
              </button>
            </section>

            {/* SECTION 2: PROFILE - Appears after generation */}
            {profile && (
              <section 
                id="profile" 
                className="terminal-container"
                style={{ marginTop: '3rem' }}
                aria-label="Your learning profile"
              >
                <h2>━━━ YOUR LEARNING PROFILE ━━━</h2>
                
                <div style={{ 
                  background: 'rgba(255, 214, 10, 0.05)',
                  border: '1px solid var(--border-color)',
                  padding: '1.5rem',
                  marginBottom: '2rem',
                  fontSize: '1.1rem',
                  lineHeight: '1.8'
                }}>
                  {profile}
                </div>

                {!showRefinement ? (
                  <>
                    <p style={{ marginBottom: '1.5rem' }}>Does this match where you are?</p>
                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                      <button
                        onClick={handleApproveProfile}
                        className="terminal-button"
                      >
                        Yes, Show Me My Plan
                      </button>
                      <button
                        onClick={() => setShowRefinement(true)}
                        className="terminal-button"
                      >
                        Not Quite
                      </button>
                    </div>
                  </>
                ) : (
                  <div>
                    <p style={{ marginBottom: '1rem' }}>What should we adjust?</p>
                    <textarea
                      placeholder="e.g., I'm more hands-on, not just reading..."
                      maxLength={200}
                      value={userCorrection}
                      onChange={(e) => setUserCorrection(e.target.value)}
                      style={{
                        width: '100%',
                        minHeight: '100px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-primary)',
                        fontFamily: 'inherit',
                        padding: '1rem',
                        fontSize: '1rem',
                        marginBottom: '1rem'
                      }}
                    />
                    <button
                      onClick={handleRefineProfile}
                      className="terminal-button"
                    >
                      Update My Profile
                    </button>
                  </div>
                )}
              </section>
            )}

            {/* ERROR DISPLAY - Shows when API calls fail */}
            {error && (
              <section 
                className="terminal-container"
                style={{ 
                  marginTop: '3rem',
                  borderColor: '#ff6b6b',
                  background: 'rgba(255, 107, 107, 0.1)'
                }}
                role="alert"
                aria-live="assertive"
              >
                <h2 style={{ color: '#ff6b6b' }}>━━━ ERROR ━━━</h2>
                
                <p style={{ 
                  fontSize: '1.1rem',
                  lineHeight: '1.6',
                  marginBottom: '1.5rem'
                }}>
                  {error}
                </p>

                {retryAllowed && retryAction && (
                  <button
                    onClick={() => {
                      setError(null);
                      retryAction();
                    }}
                    className="terminal-button"
                  >
                    Try Again
                  </button>
                )}
              </section>
            )}

            {/* SECTION 3: PROGRESSIVE LOADING - Appears below profile during generation */}
            {isGeneratingBriefing && !briefing && (
              <section 
                id="loading" 
                className="terminal-container"
                style={{ marginTop: '3rem' }}
                aria-label="Generating your learning path"
                aria-live="polite"
              >
                <h2>━━━ GENERATING YOUR LEARNING PATH ━━━</h2>
                
                <div style={{ 
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.5rem',
                  marginTop: '2rem'
                }}>
                  {/* Step 1: Navigator reasoning */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    opacity: loadingStep >= 0 ? 1 : 0.3,
                    transition: 'opacity 0.5s ease'
                  }}>
                    <div style={{ 
                      fontSize: '1.5rem',
                      minWidth: '2rem'
                    }}>
                      {loadingStep > 0 ? '✓' : '🧠'}
                    </div>
                    <div>
                      <div style={{ 
                        fontWeight: 'bold',
                        marginBottom: '0.25rem',
                        color: loadingStep > 0 ? 'var(--text-primary)' : 'var(--accent-primary)'
                      }}>
                        Navigator agent is reasoning about your profile...
                      </div>
                      <div style={{ 
                        fontSize: '0.9rem',
                        color: 'var(--text-dim)',
                        lineHeight: '1.5'
                      }}>
                        Analyzing your experience level, goals, and learning style
                      </div>
                    </div>
                  </div>

                  {/* Step 2: Curating resources */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    opacity: loadingStep >= 1 ? 1 : 0.3,
                    transition: 'opacity 0.5s ease'
                  }}>
                    <div style={{ 
                      fontSize: '1.5rem',
                      minWidth: '2rem'
                    }}>
                      {loadingStep > 1 ? '✓' : '📚'}
                    </div>
                    <div>
                      <div style={{ 
                        fontWeight: 'bold',
                        marginBottom: '0.25rem',
                        color: loadingStep > 1 ? 'var(--text-primary)' : loadingStep >= 1 ? 'var(--accent-primary)' : 'var(--text-dim)'
                      }}>
                        Curating resources from our directory...
                      </div>
                      <div style={{ 
                        fontSize: '0.9rem',
                        color: 'var(--text-dim)',
                        lineHeight: '1.5'
                      }}>
                        Filtering 23 verified resources to match your needs
                      </div>
                    </div>
                  </div>

                  {/* Step 3: Sequencing path */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    opacity: loadingStep >= 2 ? 1 : 0.3,
                    transition: 'opacity 0.5s ease'
                  }}>
                    <div style={{ 
                      fontSize: '1.5rem',
                      minWidth: '2rem'
                    }}>
                      {loadingStep > 2 ? '✓' : '🎯'}
                    </div>
                    <div>
                      <div style={{ 
                        fontWeight: 'bold',
                        marginBottom: '0.25rem',
                        color: loadingStep > 2 ? 'var(--text-primary)' : loadingStep >= 2 ? 'var(--accent-primary)' : 'var(--text-dim)'
                      }}>
                        Sequencing your personalized path...
                      </div>
                      <div style={{ 
                        fontSize: '0.9rem',
                        color: 'var(--text-dim)',
                        lineHeight: '1.5'
                      }}>
                        Ordering resources from foundational to advanced
                      </div>
                    </div>
                  </div>

                  {/* Step 4: Creating PDF */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    opacity: loadingStep >= 3 ? 1 : 0.3,
                    transition: 'opacity 0.5s ease'
                  }}>
                    <div style={{ 
                      fontSize: '1.5rem',
                      minWidth: '2rem'
                    }}>
                      📄
                    </div>
                    <div>
                      <div style={{ 
                        fontWeight: 'bold',
                        marginBottom: '0.25rem',
                        color: loadingStep >= 3 ? 'var(--accent-primary)' : 'var(--text-dim)'
                      }}>
                        Creating your Command Briefing PDF...
                      </div>
                      <div style={{ 
                        fontSize: '0.9rem',
                        color: 'var(--text-dim)',
                        lineHeight: '1.5'
                      }}>
                        Generating downloadable plan with clickable links
                      </div>
                    </div>
                  </div>
                </div>

                {/* Animated spinner */}
                <div style={{
                  marginTop: '2rem',
                  textAlign: 'center',
                  fontSize: '0.9rem',
                  color: 'var(--text-dim)'
                }}>
                  <div className="spinner" style={{
                    display: 'inline-block',
                    width: '20px',
                    height: '20px',
                    border: '2px solid var(--border-color)',
                    borderTopColor: 'var(--accent-primary)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    marginRight: '0.5rem'
                  }} />
                  This usually takes 20-30 seconds...
                </div>
              </section>
            )}

            {/* SECTION 4: BRIEFING - Visual Resource Cards */}
            {briefing && (
              <section 
                id="briefing" 
                className="terminal-container"
                style={{ marginTop: '3rem' }}
                aria-label="Your learning plan"
              >
                <h2>━━━ YOUR LEARNING PLAN ━━━</h2>
                
                <div className="learning-path-cards">
                  {briefing.recommended_resources.map((resource: LearningResource, idx: number) => (
                    <article key={resource.resource_id} className="resource-card">
                      {/* Card Header */}
                      <div className="card-header">
                        <div className="card-category">{resource.format.toUpperCase()}</div>
                        <div className="card-number">RESOURCE {idx + 1}/{briefing.recommended_resources.length}</div>
                      </div>

                      {/* Card Title */}
                      <h3 className="card-title">{resource.resource_name}</h3>
                      <div className="card-provider">{resource.provider}</div>

                      {/* Badges */}
                      <div className="card-badges">
                        <span className="badge badge-hours">{resource.estimated_hours}h</span>
                        <span className="badge badge-difficulty">{resource.difficulty}</span>
                        <span className="badge badge-format">{resource.format}</span>
                      </div>

                      {/* Reasoning Panel */}
                      <div className="reasoning-panel">
                        <div className="reasoning-header">WHY THIS RESOURCE</div>
                        <p className="reasoning-text">{resource.why_for_you}</p>
                      </div>

                      {/* Action Button */}
                      <a 
                        href={resource.resource_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="resource-link-btn"
                      >
                        START_LEARNING →
                      </a>
                    </article>
                  ))}
                </div>

                {/* Summary Section */}
                <div className="path-summary">
                  <div className="summary-stat">
                    <span className="stat-label">TOTAL TIME:</span>
                    <span className="stat-value">{briefing.total_estimated_hours} hours</span>
                  </div>
                  <div className="summary-stat">
                    <span className="stat-label">RESOURCES:</span>
                    <span className="stat-value">{briefing.recommended_resources.length} curated</span>
                  </div>
                  <div className="summary-stat">
                    <span className="stat-label">NEXT STEP:</span>
                    <span className="stat-value">{briefing.approach_guidance || 'Start with Resource 1'}</span>
                  </div>
                </div>

                {/* Download Button or Warning */}
                {briefing.pdf_url ? (
                  <button
                    className="terminal-button"
                    style={{ width: '100%', marginTop: '2rem' }}
                    onClick={() => window.open(briefing.pdf_url, '_blank')}
                  >
                    Download My Plan (PDF)
                  </button>
                ) : briefing.pdf_warning ? (
                  <div style={{
                    marginTop: '2rem',
                    padding: '1rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '4px',
                    color: 'var(--text-dim)',
                    fontSize: '0.9rem'
                  }}>
                    ⚠️ {briefing.pdf_warning}
                  </div>
                ) : null}

                {/* Session warning */}
                <div
                  role="alert"
                  className="terminal-alert"
                  style={{ marginTop: '2rem' }}
                >
                  Privacy reminder: This session is temporary. Download your plan before closing this page.
                </div>
              </section>
            )}
          </div>
          </>
        )}

        {/* About Modal */}
        {showAboutModal && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(10, 17, 40, 0.95)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '1rem'
            }}
            onClick={() => setShowAboutModal(false)}
            role="dialog"
            aria-modal="true"
            aria-labelledby="about-modal-title"
          >
            <div
              className="terminal-container"
              style={{
                maxWidth: '600px',
                width: '100%',
                position: 'relative'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 
                id="about-modal-title"
                style={{ 
                  marginBottom: '1.5rem',
                  fontSize: '1.3rem',
                  borderBottom: '1px solid var(--border-color)',
                  paddingBottom: '0.5rem'
                }}
              >
                ABOUT CLEW DIRECTIVE
              </h2>

              <div style={{ 
                display: 'flex',
                flexDirection: 'column',
                gap: '1.5rem',
                marginBottom: '2rem'
              }}>
                <div>
                  <h3 style={{ 
                    fontSize: '0.9rem',
                    color: 'var(--text-primary)',
                    marginBottom: '0.5rem',
                    fontWeight: 'bold'
                  }}>
                    OUR PHILOSOPHY:
                  </h3>
                  <p style={{ 
                    color: 'var(--text-dim)',
                    lineHeight: '1.7',
                    fontSize: '0.95rem'
                  }}>
                    We don't sell courses. We curate freely accessible resources from universities, official documentation, and industry experts. Some courses offer optional paid certificates for credentials.
                  </p>
                </div>

                <div>
                  <h3 style={{ 
                    fontSize: '0.9rem',
                    color: 'var(--text-primary)',
                    marginBottom: '0.5rem',
                    fontWeight: 'bold'
                  }}>
                    YOUR PRIVACY:
                  </h3>
                  <p style={{ 
                    color: 'var(--text-dim)',
                    lineHeight: '1.7',
                    fontSize: '0.95rem'
                  }}>
                    This session is temporary. No cookies, no accounts, no tracking. Your learning plan is yours to keep.
                  </p>
                </div>

                <div>
                  <h3 style={{ 
                    fontSize: '0.9rem',
                    color: 'var(--text-primary)',
                    marginBottom: '0.5rem',
                    fontWeight: 'bold'
                  }}>
                    HOW WE CURATE:
                  </h3>
                  <p style={{ 
                    color: 'var(--text-dim)',
                    lineHeight: '1.7',
                    fontSize: '0.95rem'
                  }}>
                    Every resource passes our 5-gate quality check and comes from trusted, authoritative sources. We verify availability weekly.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setShowAboutModal(false)}
                className="terminal-button"
                style={{ width: '100%' }}
                aria-label="Close about dialog"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
