#!/usr/bin/env node
/**
 * Dynamic Tool Loader MCP Server
 * 
 * This MCP server can dynamically load and serve tools from a directory
 * without requiring Claude Code to restart. New tools can be added at runtime.
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { z } = require('zod');
const fs = require('fs').promises;
const path = require('path');
const TOOLS_DIR = path.join(__dirname, 'generated_tools');

class DynamicToolLoader {
  constructor() {
    this.server = new Server({
      name: 'dynamic-tool-loader',
      version: '1.0.0',
    }, {
      capabilities: {
        tools: {},
      },
    });
    
    this.tools = new Map();
    this.setupHandlers();
  }

  async loadTools() {
    try {
      // Ensure tools directory exists
      await fs.mkdir(TOOLS_DIR, { recursive: true });
      
      // Load all tool definitions
      const files = await fs.readdir(TOOLS_DIR);
      const toolFiles = files.filter(f => f.endsWith('.json'));
      
      for (const file of toolFiles) {
        try {
          const content = await fs.readFile(path.join(TOOLS_DIR, file), 'utf-8');
          const toolDef = JSON.parse(content);
          
          if (toolDef.name && toolDef.description && toolDef.implementation) {
            this.tools.set(toolDef.name, toolDef);
            console.error(`Loaded tool: ${toolDef.name}`);
          }
        } catch (e) {
          console.error(`Failed to load tool ${file}:`, e);
        }
      }
    } catch (e) {
      console.error('Failed to load tools:', e);
    }
  }

  setupHandlers() {
    // List available tools
    this.server.setRequestHandler('tools/list', async () => {
      // Reload tools on each request to pick up new ones
      await this.loadTools();
      
      const tools = Array.from(this.tools.values()).map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema || {
          type: 'object',
          properties: {},
        },
      }));
      
      return { tools };
    });

    // Execute a tool
    this.server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      // Reload tools to pick up any updates
      await this.loadTools();
      
      const tool = this.tools.get(name);
      if (!tool) {
        throw new Error(`Tool ${name} not found`);
      }
      
      try {
        // Execute the tool implementation
        // In a real implementation, this would safely execute the code
        const impl = new Function('args', tool.implementation);
        const result = await impl(args);
        
        return {
          content: [{
            type: 'text',
            text: JSON.stringify(result, null, 2),
          }],
        };
      } catch (e) {
        return {
          content: [{
            type: 'text',
            text: `Error executing tool: ${e.message}`,
          }],
          isError: true,
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Dynamic tool loader MCP server running');
    
    // Initial tool load
    await this.loadTools();
  }
}

// Run the server
const loader = new DynamicToolLoader();
loader.run().catch(console.error);