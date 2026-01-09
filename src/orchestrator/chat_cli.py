#!/usr/bin/env python3
"""
Interactive Chat CLI for Testing Orchestrator
"""

import asyncio
from src.orchestrator.state_graph import StateGraphOrchestrator
from colorama import init, Fore, Style
import sys

init(autoreset=True)  # Auto-reset colors

class ChatCLI:
    """Interactive chat interface for testing"""
    
    def __init__(self):
        self.orchestrator = StateGraphOrchestrator()
        self.session_active = True
    
    def print_banner(self):
        """Print welcome banner"""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}🚀 TITAN SUPPLY CHAIN AI - Interactive Chat")
        print(f"{Fore.CYAN}{'='*70}\n")
        print(f"{Fore.YELLOW}Commands:")
        print(f"  {Fore.GREEN}/clear{Fore.RESET}  - Clear conversation history")
        print(f"  {Fore.GREEN}/history{Fore.RESET} - Show conversation history")
        print(f"  {Fore.GREEN}/stats{Fore.RESET}  - Show last query statistics")
        print(f"  {Fore.GREEN}/exit{Fore.RESET}   - Exit chat")
        print(f"\n{Fore.CYAN}{'='*70}\n")
    
    async def process_query(self, query: str):
        """Process user query through orchestrator"""
        print(f"\n{Fore.BLUE}🤔 Processing...\n")
        
        result = await self.orchestrator.run(query)
        
        # Print response
        print(f"{Fore.GREEN}🤖 TITAN:")
        print(f"{Fore.WHITE}{result['answer']}\n")
        
        # Print metadata
        print(f"{Fore.CYAN}📊 Metadata:")
        print(f"   Intent: {result['intent']}")
        print(f"   Sources: {', '.join(result['sources'])}")
        print(f"   Processing Time: {result['processing_time']['total']:.2f}s")
        print(f"   Compression: {result['compression_ratio']:.1%}")
        print(f"   Node Path: {' → '.join(result['node_sequence'])}")
        
        if result['errors']:
            print(f"{Fore.RED}   Errors: {', '.join(result['errors'])}")
        
        self.last_result = result
    
    def show_history(self):
        """Show conversation history"""
        history = self.orchestrator.memory.get_last_n_messages(10)
        
        print(f"\n{Fore.CYAN}📜 Conversation History ({len(history)} messages):")
        print(f"{Fore.CYAN}{'='*70}\n")
        
        for msg in history:
            role_emoji = "👤" if msg['role'] == "user" else "🤖"
            role_color = Fore.YELLOW if msg['role'] == "user" else Fore.GREEN
            print(f"{role_color}{role_emoji} {msg['role'].upper()}: {Fore.WHITE}{msg['content'][:100]}...")
        
        print()
    
    def show_stats(self):
        """Show last query statistics"""
        if not hasattr(self, 'last_result'):
            print(f"{Fore.RED}No queries yet!\n")
            return
        
        result = self.last_result
        
        print(f"\n{Fore.CYAN}📊 Last Query Statistics:")
        print(f"{Fore.CYAN}{'='*70}\n")
        
        print(f"{Fore.YELLOW}Intent:{Fore.RESET} {result['intent']}")
        print(f"{Fore.YELLOW}Entities:{Fore.RESET} {', '.join(result['entities']) if result['entities'] else 'None'}")
        print(f"{Fore.YELLOW}Confidence:{Fore.RESET} {result['confidence']:.2f}")
        print(f"\n{Fore.YELLOW}Context Sizes:")
        for ctx_type, size in result['context_used'].items():
            print(f"   {ctx_type}: {size} chars")
        
        print(f"\n{Fore.YELLOW}Processing Times:")
        for stage, time in result['processing_time'].items():
            print(f"   {stage}: {time:.3f}s")
        
        print()
    
    async def run(self):
        """Main chat loop"""
        self.print_banner()
        
        while self.session_active:
            try:
                # Get user input
                user_input = input(f"{Fore.YELLOW}👤 You: {Fore.RESET}").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command == '/exit':
                        print(f"\n{Fore.CYAN}👋 Goodbye!\n")
                        break
                    
                    elif command == '/clear':
                        self.orchestrator.memory.clear()
                        print(f"\n{Fore.GREEN}✅ Conversation history cleared!\n")
                    
                    elif command == '/history':
                        self.show_history()
                    
                    elif command == '/stats':
                        self.show_stats()
                    
                    else:
                        print(f"\n{Fore.RED}Unknown command: {user_input}\n")
                    
                    continue
                
                # Process query
                await self.process_query(user_input)
            
            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}👋 Goodbye!\n")
                break
            
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error: {str(e)}\n")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run interactive chat"""
    chat = ChatCLI()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
