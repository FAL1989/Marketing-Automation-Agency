import { FC } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PrivateRoute } from '../components/PrivateRoute';
import { Login } from '../pages/Login';
import { Dashboard } from '../pages/Dashboard';
import { TemplateListPage } from '../pages/TemplateListPage';
import { TemplateEditorPage } from '../pages/TemplateEditorPage';
import { ContentGeneratorPage } from '../pages/ContentGeneratorPage';
import { GenerationHistoryPage } from '../pages/GenerationHistoryPage';
import { GenerationDetails } from '../pages/GenerationDetails';
import { PromptConfigPage } from '../pages/PromptConfigPage';
import { Analytics } from '../pages/Analytics';

export const AppRoutes: FC = () => {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route path="/dashboard" element={
                <PrivateRoute>
                    <Dashboard />
                </PrivateRoute>
            } />
            
            <Route path="/templates" element={
                <PrivateRoute>
                    <TemplateListPage />
                </PrivateRoute>
            } />
            
            <Route path="/templates/new" element={
                <PrivateRoute>
                    <TemplateEditorPage />
                </PrivateRoute>
            } />
            
            <Route path="/templates/edit/:id" element={
                <PrivateRoute>
                    <TemplateEditorPage />
                </PrivateRoute>
            } />
            
            <Route path="/generator" element={
                <PrivateRoute>
                    <ContentGeneratorPage />
                </PrivateRoute>
            } />
            
            <Route path="/history" element={
                <PrivateRoute>
                    <GenerationHistoryPage />
                </PrivateRoute>
            } />
            
            <Route path="/history/:id" element={
                <PrivateRoute>
                    <GenerationDetails />
                </PrivateRoute>
            } />
            
            <Route path="/prompts" element={
                <PrivateRoute>
                    <PromptConfigPage />
                </PrivateRoute>
            } />
            
            <Route path="/analytics" element={
                <PrivateRoute>
                    <Analytics />
                </PrivateRoute>
            } />
            
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}; 