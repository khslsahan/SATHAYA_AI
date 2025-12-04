import { useState } from 'react'
import Head from 'next/head'
import ChatInterface from '@/components/ChatInterface'

export default function Home() {
  return (
    <>
      <Head>
        <title>Lanka Legal Analyst</title>
        <meta name="description" content="Agentic RAG system for Sri Lankan Law" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              🇱🇰 Lanka Legal Analyst
            </h1>
            <p className="text-lg text-gray-600">
              Your intelligent legal research assistant for Sri Lankan Law
            </p>
          </header>
          <ChatInterface />
        </div>
      </main>
    </>
  )
}

