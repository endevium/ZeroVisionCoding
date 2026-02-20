import React, { useState, useEffect } from 'react';
import { motion as Motion, AnimatePresence } from 'motion/react';
import placeholder from './assets/ZVPLACEHOLDER.png'
import { 
  Menu, 
  X, 
  Code, 
  Cpu, 
  Eye, 
  ArrowRight, 
  Mail, 
  Github, 
  Linkedin, 
  Twitter,
  CheckCircle,
  Accessibility,
  Heart,
  Sparkles,
  Zap,
  Download,
  Monitor,
  FileCode,
  Terminal
} from 'lucide-react';
import logoImage from './assets/zvlogo.png';

// Dynamic Background Component
const DynamicBackground = () => {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {/* Deep base gradient */}
      <div className="absolute inset-0 bg-black"></div>
      
      {/* Animated glowing orbs */}
      <Motion.div 
        animate={{ 
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
          rotate: [0, 45, 0]
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-[20%] -left-[10%] w-[70vw] h-[70vw] rounded-full bg-purple-900/20 blur-[120px]"
      />
      
      <Motion.div 
        animate={{ 
          scale: [1, 1.5, 1],
          opacity: [0.2, 0.4, 0.2],
          x: [0, 100, 0]
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        className="absolute top-[20%] -right-[20%] w-[60vw] h-[60vw] rounded-full bg-indigo-900/20 blur-[100px]"
      />
      
      <Motion.div 
        animate={{ 
          scale: [1, 1.3, 1],
          opacity: [0.2, 0.5, 0.2],
          y: [0, -50, 0]
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 5 }}
        className="absolute -bottom-[20%] left-[20%] w-[80vw] h-[80vw] rounded-full bg-violet-900/10 blur-[120px]"
      />
      
      {/* Noise texture overlay */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay"></div>
    </div>
  );
};

// Navigation Component
const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Home', href: '#home' },
    { name: 'Features', href: '#features' },
    { name: 'Downloads', href: '#downloads' },
    { name: 'About', href: '#about' },
    { name: 'Contact', href: '#contact' },
  ];

  return (
    <nav className={`fixed w-full z-50 transition-all duration-500 ${scrolled ? 'bg-black/40 backdrop-blur-xl border-b border-white/5 py-3 shadow-lg shadow-purple-900/10' : 'bg-transparent py-6'}`}>
      <div className="container mx-auto px-4 md:px-6 flex justify-between items-center">
        <a href="#" className="flex items-center gap-3 group relative z-50">
          <div className="h-10 overflow-visible relative flex items-center">
            {/* Logo Glow Effect */}
            <div className="absolute inset-0 bg-purple-500/0 group-hover:bg-purple-500/0 blur-xl transition-all duration-500"></div>
            <img 
              src={logoImage} 
              alt="Zero Vision Logo" 
              className="h-full w-auto object-contain relative z-10 transition-all duration-500 drop-shadow-[0_0_0_rgba(168,85,247,0)] group-hover:drop-shadow-[0_0_15px_rgba(236,72,153,0.8)]"
              style={{
                filter: "drop-shadow(0 0 5px rgba(168, 85, 247, 0.6))" 
              }}
            />
          </div>
        </a>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a 
              key={link.name} 
              href={link.href} 
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors relative group"
            >
              {link.name}
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-300 group-hover:w-full opacity-0 group-hover:opacity-100"></span>
            </a>
          ))}
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="md:hidden text-slate-300 hover:text-white transition-colors relative z-50"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile Nav */}
      <AnimatePresence>
        {isOpen && (
          <Motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: '100vh' }}
            exit={{ opacity: 0, height: 0 }}
            className="fixed inset-0 top-0 z-40 md:hidden bg-black/95 backdrop-blur-2xl border-b border-white/10 pt-24"
          >
            <div className="container mx-auto px-4 flex flex-col gap-6">
              {navLinks.map((link, i) => (
                <Motion.a 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.1 }}
                  key={link.name} 
                  href={link.href}
                  onClick={() => setIsOpen(false)}
                  className="text-2xl font-bold text-slate-300 hover:text-white hover:pl-2 transition-all"
                >
                  <span className="text-purple-500 mr-2">0{i + 1}.</span> {link.name}
                </Motion.a>
              ))}
              <Motion.a 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                href="#downloads" 
                onClick={() => setIsOpen(false)}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-5 py-4 rounded-xl text-center font-bold mt-4 shadow-lg shadow-purple-900/40"
              >
                Download App
              </Motion.a>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

// Hero Component
const Hero = () => {
  return (
    <section id="home" className="relative min-h-screen flex items-center pt-20 overflow-hidden">
      <div className="container mx-auto px-4 md:px-6 relative z-10 py-20">
        <div className="flex flex-col md:flex-row items-center gap-16 md:gap-24">
          <div className="w-full md:w-1/2 space-y-8">
            <Motion.div 
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-900/30 border border-purple-500/30 text-purple-200 text-xs font-bold tracking-widest uppercase backdrop-blur-md shadow-[0_0_15px_rgba(168,85,247,0.3)]"
            >
              <Sparkles size={12} className="text-purple-300 animate-pulse" />
              <span>Future of Accessibility</span>
            </Motion.div>
            
            <Motion.h1 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-none text-white"
            >
              Code Beyond <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-[length:200%_auto] animate-gradient-x">
                Sight.
              </span>
            </Motion.h1>
            
            <Motion.p 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-slate-300 max-w-lg leading-relaxed font-light border-l-2 border-purple-500/30 pl-6"
            >
              Zero Vision Coding transforms the abstract into the tactile. An AI-enhanced Arduino platform forging a new reality for visually impaired developers.
            </Motion.p>
            
            <Motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-5 pt-4"
            >
              <a href="#downloads" className="group relative inline-flex justify-center items-center gap-3 bg-white text-black px-8 py-4 rounded-full font-bold text-lg transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(255,255,255,0.3)] overflow-hidden">
                <span className="absolute inset-0 bg-gradient-to-r from-slate-100 to-slate-300 opacity-0 group-hover:opacity-100 transition-opacity"></span>
                <span className="relative z-10 flex items-center gap-2">Download Now <Download size={20} className="group-hover:translate-y-1 transition-transform" /></span>
              </a>
              <a href="#about" className="inline-flex justify-center items-center gap-3 bg-transparent border border-white/20 hover:border-purple-400 hover:bg-purple-900/10 text-white px-8 py-4 rounded-full font-medium text-lg transition-all backdrop-blur-sm">
                Learn More
              </a>
            </Motion.div>
            
            <Motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="pt-8 flex flex-wrap gap-x-8 gap-y-3 text-slate-400 text-sm font-medium"
            >
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.8)]"></div>
                <span>Screen Reader Optimized</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-pink-500 shadow-[0_0_10px_rgba(236,72,153,0.8)]"></div>
                <span>Audio Feedback</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.8)]"></div>
                <span>AI Syntax Analysis</span>
              </div>
            </Motion.div>
          </div>
          
          <div className="w-full md:w-1/2 relative">
            <Motion.div 
              initial={{ opacity: 0, scale: 0.8, rotateX: 20 }}
              animate={{ opacity: 1, scale: 1, rotateX: 0 }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="relative rounded-3xl overflow-hidden shadow-2xl shadow-purple-900/40 border border-white/10 group perspective-1000"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent z-10 opacity-80"></div>
              
              <img 
                src={placeholder} 
                alt="Visually impaired developer using braille display" 
                className="w-full h-auto object-cover aspect-[4/3] grayscale-[20%] group-hover:grayscale-0 transition-all duration-700 group-hover:scale-105"
              />
            
            </Motion.div>
            
            {/* Dynamic Elements around image */}
            <Motion.div 
              animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0.8, 0.5] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute -top-10 -right-10 w-40 h-40 bg-purple-600/30 rounded-full blur-3xl -z-10 mix-blend-screen"
            ></Motion.div>
            <Motion.div 
              animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 5, repeat: Infinity, delay: 1 }}
              className="absolute -bottom-10 -left-10 w-48 h-48 bg-indigo-600/30 rounded-full blur-3xl -z-10 mix-blend-screen"
            ></Motion.div>
          </div>
        </div>
      </div>
      
      {/* Scroll Indicator */}
      <Motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-purple-300/50 text-xs tracking-widest uppercase"
      >
        <span>Scroll</span>
        <div className="w-[1px] h-12 bg-gradient-to-b from-purple-500/50 to-transparent"></div>
      </Motion.div>
    </section>
  );
};

// Features Section
const Features = () => {
  const features = [
    {
      icon: <Cpu className="w-6 h-6 text-purple-400" />,
      title: "Arduino Keyboard",
      description: "Direct hardware interface that translates voltage readings and pin states into the Visual Studio Code IDE."
    },
    {
      icon: <Accessibility className="w-6 h-6 text-pink-400" />,
      title: "Speech Commands",
      description: "Allows the user to run commands using their voice."
    },
    {
      icon: <Zap className="w-6 h-6 text-yellow-400" />,
      title: "AI Code Analysis",
      description: "Context-aware AI that predicts errors and suggests fixes, spoken in natural language."
    },
    {
      icon: <Eye className="w-6 h-6 text-indigo-400" />,
      title: "Text-to-Speech Feedback",
      description: "Turns visual data into spoken natural language."
    }
  ];

  return (
    <section id="features" className="py-32 relative z-10">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <Motion.h2 
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-purple-400 font-bold tracking-widest uppercase text-xs mb-4"
          >
            System Capabilities
          </Motion.h2>
          <Motion.h3 
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-5xl font-black text-white mb-6"
          >
            Designed for the <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">Blind</span>
          </Motion.h3>
          <Motion.p 
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-slate-400 font-light"
          >
            We've reimagined the development environment, stripping away visual dependencies to create a pure, logic-driven workflow.
          </Motion.p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Motion.div 
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className="p-8 rounded-3xl bg-white/5 border border-white/5 hover:border-purple-500/50 hover:bg-white/10 transition-all duration-300 group relative overflow-hidden backdrop-blur-sm"
            >
              {/* Card Gradient Background */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              
              <div className="w-14 h-14 rounded-2xl bg-black/50 border border-white/10 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all duration-300 relative z-10">
                {feature.icon}
              </div>
              <h4 className="text-xl font-bold text-white mb-3 relative z-10">{feature.title}</h4>
              <p className="text-slate-400 leading-relaxed text-sm relative z-10 group-hover:text-slate-200 transition-colors">
                {feature.description}
              </p>
            </Motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Downloads Section
const Downloads = () => {
  const downloads = [
    {
      title: "Zero Vision Coding",
      version: "v2.4.0 (Stable)",
      description: "Complete development environment with built-in accessibility tools.",
      icon: <Monitor className="w-8 h-8 text-white" />,
      features: [ "Screen Reader Support", "Braille Display Drivers"],
      primary: true
    },
    {
      title: "Ollama",
      version: "v1.2.1",
      description: "Essential libraries for Artificial Intelligence.",
      icon: <Cpu className="w-8 h-8 text-purple-300" />,
      features: ["Board Definitions", "Firmware Updates", "Examples"],
      primary: false
    },
    {
      title: "Visual Studio Code Extension",
      version: "v0.9.5",
      description: "Enhanced screen reader support for complex syntax.",
      icon: <Terminal className="w-8 h-8 text-pink-300" />,
      features: ["Syntax Highlighting", "Audio Cues", "Debugging Tools"],
      primary: false
    }
  ];

  return (
    <section id="downloads" className="py-32 relative z-10">
      <div className="absolute top-0 right-0 w-full h-px bg-gradient-to-l from-transparent via-purple-500/20 to-transparent"></div>
      
      <div className="container mx-auto px-4 md:px-6">
        <div className="flex flex-col lg:flex-row gap-16 items-start">
          <div className="w-full lg:w-1/3 space-y-6">
            <Motion.div 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-purple-300 text-xs font-bold tracking-wide uppercase"
            >
              <Download size={12} />
              <span>Downloads</span>
            </Motion.div>
            
            <Motion.h2 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-4xl font-black text-white"
            >
              Get the Tools used by <span className="text-purple-400">Pros.</span>
            </Motion.h2>
            
            <Motion.p 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-lg text-slate-400 font-light leading-relaxed"
            >
              Download the latest stable release of the Zero Vision platform. Open source and free for personal use.
            </Motion.p>
            
            <Motion.div 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
            >
              <a href="#" className="text-white hover:text-purple-400 font-bold flex items-center gap-2 transition-colors">
                View Source Code on GitHub <ArrowRight size={16} />
              </a>
            </Motion.div>
          </div>
          
          <div className="w-full lg:w-2/3 grid md:grid-cols-2 gap-6">
            {/* Primary Download Card */}
            <Motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="md:col-span-2 bg-gradient-to-br from-purple-900/40 to-black/60 border border-purple-500/30 p-8 rounded-3xl relative overflow-hidden group hover:border-purple-500/60 transition-all duration-300"
            >
              <div className="absolute top-0 right-0 p-4">
                <span className="bg-purple-500/20 text-purple-200 text-xs font-bold px-2 py-1 rounded border border-purple-500/30">LATEST</span>
              </div>
              
              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
                <div className="w-16 h-16 rounded-2xl bg-purple-600 flex items-center justify-center shadow-lg shadow-purple-600/30 shrink-0">
                  <Monitor size={32} className="text-white" />
                </div>
                
                <div className="flex-1 space-y-2">
                  <h3 className="text-2xl font-bold text-white">Zero Vision Coding</h3>
                  <p className="text-purple-200 text-sm font-mono">{downloads[0].version}</p>
                  <p className="text-slate-300 text-sm">{downloads[0].description}</p>
                </div>
                
                <div className="flex flex-col gap-3 w-full md:w-auto">
                  <button className="bg-white text-purple-900 hover:bg-purple-50 font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 transition-colors">
                    <Download size={18} /> Download
                  </button>
                </div>
              </div>
            </Motion.div>
            
            {/* Secondary Cards */}
            {downloads.slice(1).map((item, index) => (
              <Motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 + index * 0.1 }}
                className="bg-white/5 border border-white/10 p-6 rounded-3xl hover:bg-white/10 hover:border-white/20 transition-all group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="w-12 h-12 rounded-xl bg-black/50 border border-white/10 flex items-center justify-center">
                    {item.icon}
                  </div>
                  <a href="#" className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center hover:bg-purple-600 hover:text-white transition-colors">
                    <Download size={14} />
                  </a>
                </div>
                
                <h3 className="text-lg font-bold text-white mb-1">{item.title}</h3>
                <p className="text-slate-500 text-xs font-mono mb-3">{item.version}</p>
                <p className="text-slate-400 text-sm mb-4 leading-relaxed">{item.description}</p>
                
                <ul className="space-y-2">
                  {item.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-xs text-slate-500">
                      <CheckCircle size={10} className="text-purple-500" /> {feature}
                    </li>
                  ))}
                </ul>
              </Motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

// About Section
const About = () => {
  return (
    <section id="about" className="py-32 relative z-10">
      <div className="container mx-auto px-4 md:px-6">
        <div className="flex flex-col lg:flex-row items-center gap-20">
          <div className="w-full lg:w-1/2">
            <Motion.div 
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8 }}
              className="relative"
            >
              {/* Glow effect behind image */}
              <div className="absolute -inset-4 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl blur-xl opacity-30 animate-pulse-slow"></div>
              
              <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl group">
                <img 
                  src="https://images.unsplash.com/photo-1559819615-9e8ae012d723?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhcmR1aW5vJTIwY2lyY3VpdCUyMGJvYXJkJTIwY2xvc2UlMjB1cHxlbnwxfHx8fDE3NzE1MTA0NDl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral" 
                  alt="Arduino circuit board close up" 
                  className="w-full h-auto object-cover grayscale brightness-75 group-hover:grayscale-0 group-hover:brightness-100 transition-all duration-700 scale-100 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex items-end p-10">
                  <div className="transform translate-y-4 group-hover:translate-y-0 transition-transform duration-500">
                    <p className="text-purple-400 font-bold text-lg mb-1">Hardware Unlocked</p>
                    <p className="text-slate-300 text-sm">Touching the future of embedded systems.</p>
                  </div>
                </div>
              </div>
            </Motion.div>
          </div>
          
          <div className="w-full lg:w-1/2 space-y-8">
            <Motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-black text-white"
            >
              The Vision
            </Motion.h2>
            
            <Motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="space-y-6 text-lg text-slate-400 font-light leading-relaxed"
            >
              <p>
                Visual impairment has historically been a gatekeeper to the world of hardware innovation. Schematics, blinking LEDs, and color-coded wires—all inaccessible.
              </p>
              <p>
                Zero Vision Coding shatters these barriers. We are building a reality where code is felt, diagrams are heard, and creativity flows without visual constraints.
              </p>
            </Motion.div>
            
            <div className="grid grid-cols-2 gap-8 pt-6 border-t border-white/10">
              <Motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3 }}
                className="space-y-1"
              >
                <h4 className="text-4xl font-bold text-white">5k+</h4>
                <p className="text-purple-400 text-sm uppercase tracking-wider font-bold">Active Devs</p>
              </Motion.div>
              <Motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 }}
                className="space-y-1"
              >
                <h4 className="text-4xl font-bold text-white">120+</h4>
                <p className="text-purple-400 text-sm uppercase tracking-wider font-bold">Open Projects</p>
              </Motion.div>
            </div>
            
            <Motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5 }}
              className="pt-8"
            >
              <a href="#contact" className="text-white font-bold hover:text-purple-400 inline-flex items-center gap-3 transition-colors group text-lg">
                Read our manifesto <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </a>
            </Motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};

// Contact Section
const Contact = () => {
  return (
    <section id="contact" className="py-32 relative z-10 overflow-hidden">
      {/* Background flare */}
      <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-[100px] -z-10 translate-x-1/2"></div>
      
      <div className="container mx-auto px-4 md:px-6">
        <div className="flex flex-col lg:flex-row gap-16 lg:gap-24">
          <div className="w-full lg:w-5/12 space-y-10">
            <div>
              <h2 className="text-purple-400 font-bold tracking-widest uppercase text-xs mb-4">Connect With Us</h2>
              <h3 className="text-4xl md:text-5xl font-black text-white mb-6">Join the Revolution</h3>
              <p className="text-lg text-slate-400 font-light">
                Whether you're a developer, an educator, or an ally, your voice matters in building an accessible future.
              </p>
            </div>
            
            <div className="space-y-8">
              <div className="flex items-start gap-5 group">
                <div className="w-14 h-14 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-purple-400 group-hover:bg-purple-600 group-hover:text-white transition-all duration-300 shrink-0">
                  <Mail size={24} />
                </div>
                <div>
                  <h4 className="font-bold text-white text-lg mb-1">Email Us</h4>
                  <p className="text-slate-500 text-sm font-mono group-hover:text-purple-300 transition-colors">hello@zerovisioncoding.com</p>
                </div>
              </div>
              
              <div className="flex items-start gap-5 group">
                <div className="w-14 h-14 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-pink-400 group-hover:bg-pink-600 group-hover:text-white transition-all duration-300 shrink-0">
                  <Heart size={24} />
                </div>
                <div>
                  <h4 className="font-bold text-white text-lg mb-1">Support the Cause</h4>
                  <p className="text-slate-500 text-sm group-hover:text-pink-300 transition-colors">Help us democratize technology through open-source contribution.</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="w-full lg:w-7/12">
            <Motion.div 
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-white/5 backdrop-blur-xl p-8 md:p-12 rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden group"
            >
              <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/20 rounded-full blur-3xl -z-10 group-hover:bg-purple-600/30 transition-all duration-500"></div>
              
              <h3 className="text-2xl font-bold text-white mb-8">Send us a message</h3>
              <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label htmlFor="name" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Full Name</label>
                    <input 
                      type="text" 
                      id="name" 
                      className="w-full px-4 py-4 rounded-xl bg-black/40 border border-white/10 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all placeholder:text-slate-700 focus:bg-black/60"
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="email" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Email Address</label>
                    <input 
                      type="email" 
                      id="email" 
                      className="w-full px-4 py-4 rounded-xl bg-black/40 border border-white/10 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all placeholder:text-slate-700 focus:bg-black/60"
                      placeholder="jane@example.com"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label htmlFor="message" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Message</label>
                  <textarea 
                    id="message" 
                    rows={4}
                    className="w-full px-4 py-4 rounded-xl bg-black/40 border border-white/10 text-white focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all resize-none placeholder:text-slate-700 focus:bg-black/60"
                    placeholder="How can we help you?"
                  ></textarea>
                </div>
                
                <button 
                  type="submit" 
                  className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-4 rounded-xl shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] relative overflow-hidden group/btn"
                >
                  <span className="relative z-10">Send Message</span>
                  <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300"></div>
                </button>
              </form>
            </Motion.div>
          </div>
        </div>
      </div>
    </section>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="relative z-10 bg-black/80 backdrop-blur-xl text-slate-400 py-20 border-t border-white/10">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          <div className="space-y-6">
            <a href="#" className="block h-12 w-48 opacity-80 hover:opacity-100 transition-opacity group">
              <img 
                src={logoImage} 
                alt="Zero Vision Logo" 
                className="h-full w-auto object-contain object-left transition-all duration-500"
                style={{
                  filter: "drop-shadow(0 0 5px rgba(168, 85, 247, 0.4))" 
                }}
              />
            </a>
            <p className="text-slate-500 text-sm leading-relaxed max-w-xs">
              Empowering visually impaired developers to build the future of IoT and embedded systems.
            </p>
            <div className="flex gap-4 pt-2">
              <a href="#" className="w-10 h-10 rounded-full bg-white/5 border border-white/5 flex items-center justify-center hover:bg-purple-600 hover:text-white transition-all hover:scale-110">
                <Twitter size={18} />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/5 border border-white/5 flex items-center justify-center hover:bg-white hover:text-black transition-all hover:scale-110">
                <Github size={18} />
              </a>
              <a href="#" className="w-10 h-10 rounded-full bg-white/5 border border-white/5 flex items-center justify-center hover:bg-blue-600 hover:text-white transition-all hover:scale-110">
                <Linkedin size={18} />
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-8 text-sm uppercase tracking-wider">Quick Links</h4>
            <ul className="space-y-4 text-sm">
              <li><a href="#home" className="hover:text-purple-400 transition-colors flex items-center gap-2 group"><span className="w-1 h-1 bg-purple-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></span> Home</a></li>
              <li><a href="#about" className="hover:text-purple-400 transition-colors flex items-center gap-2 group"><span className="w-1 h-1 bg-purple-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></span> About Us</a></li>
              <li><a href="#features" className="hover:text-purple-400 transition-colors flex items-center gap-2 group"><span className="w-1 h-1 bg-purple-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></span> Features</a></li>
              <li><a href="#contact" className="hover:text-purple-400 transition-colors flex items-center gap-2 group"><span className="w-1 h-1 bg-purple-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></span> Contact</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-8 text-sm uppercase tracking-wider">Resources</h4>
            <ul className="space-y-4 text-sm">
              <li><a href="#" className="hover:text-purple-400 transition-colors">Community Forum</a></li>
              <li><a href="#" className="hover:text-purple-400 transition-colors">Developer Blog</a></li>
              <li><a href="#" className="hover:text-purple-400 transition-colors">Accessibility Guides</a></li>
              <li><a href="#" className="hover:text-purple-400 transition-colors">Hardware Support</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-8 text-sm uppercase tracking-wider">Newsletter</h4>
            <p className="text-slate-500 text-sm mb-4">Subscribe for the latest updates.</p>
            <form className="flex flex-col gap-3" onSubmit={(e) => e.preventDefault()}>
              <input 
                type="email" 
                placeholder="Enter your email" 
                className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white focus:border-purple-500 focus:outline-none transition-colors"
              />
              <button className="w-full bg-purple-700 hover:bg-purple-600 text-white font-bold py-3 rounded-lg transition-colors shadow-lg shadow-purple-900/20">
                Subscribe
              </button>
            </form>
          </div>
        </div>
        
        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-6 text-xs text-slate-600 font-medium uppercase tracking-wider">
          <p>&copy; {new Date().getFullYear()} Zero Vision Coding. All rights reserved.</p>
          <div className="flex gap-8">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Accessibility</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

// Main App Component
const App = () => {
  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-purple-500/30 selection:text-purple-200">
      <DynamicBackground />
      <Navbar />
      <Hero />
      <Features />
      <Downloads />
      <About />
      <Contact />
      <Footer />
    </div>
  );
};

export default App;
