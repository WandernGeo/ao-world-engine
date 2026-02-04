'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface SceneGeneratorProps {
    locationId: string;
    locationName: string;
    currentTick: number;
    apiBaseUrl: string;
}

export function SceneGenerator({
    locationId,
    locationName,
    currentTick,
    apiBaseUrl,
}: SceneGeneratorProps) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [sceneImage, setSceneImage] = useState<string | null>(null);
    const [sceneDescription, setSceneDescription] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const generateScene = async () => {
        setIsGenerating(true);
        setError(null);

        try {
            const response = await fetch(`${apiBaseUrl}/api/scene/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    location_id: locationId,
                    tick: currentTick,
                    style: 'signal_noir',
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to generate scene');
            }

            const data = await response.json();
            setSceneImage(data.image_url || data.image_base64);
            setSceneDescription(data.description);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            // Fallback: generate with Gemini description only
            try {
                const descResponse = await fetch(`${apiBaseUrl}/api/scene/describe`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        location_id: locationId,
                        tick: currentTick,
                    }),
                });
                if (descResponse.ok) {
                    const descData = await descResponse.json();
                    setSceneDescription(descData.description);
                }
            } catch {
                // Ignore fallback errors
            }
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <Card className="bg-zinc-900/90 border-purple-500/30 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-purple-400 font-mono text-sm flex items-center gap-2">
                    <span className="text-lg">🎨</span> SCENE GENERATOR
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Location Info */}
                <div className="p-3 bg-black/50 rounded border border-purple-500/20">
                    <div className="text-sm text-zinc-400">Current Location</div>
                    <div className="font-mono text-purple-300 text-lg">{locationName}</div>
                    <div className="text-xs text-zinc-600 font-mono">ID: {locationId}</div>
                </div>

                {/* Generate Button */}
                <Button
                    onClick={generateScene}
                    disabled={isGenerating}
                    className="w-full bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500"
                >
                    {isGenerating ? (
                        <>
                            <span className="animate-spin mr-2">⚡</span>
                            Generating with Gemini 2.5 Flash...
                        </>
                    ) : (
                        <>🖼 Generate Scene Image</>
                    )}
                </Button>

                {/* Error Display */}
                {error && (
                    <div className="p-2 bg-red-900/50 border border-red-500/30 rounded text-red-300 text-sm">
                        ⚠️ {error}
                    </div>
                )}

                {/* Scene Description */}
                {sceneDescription && (
                    <div className="p-3 bg-black/50 rounded border border-zinc-700">
                        <div className="text-xs text-zinc-500 mb-1">Scene Description</div>
                        <div className="text-sm text-zinc-300 italic">{sceneDescription}</div>
                    </div>
                )}

                {/* Scene Image */}
                {sceneImage && (
                    <div className="relative">
                        <img
                            src={sceneImage.startsWith('data:') ? sceneImage : `data:image/png;base64,${sceneImage}`}
                            alt={`${locationName} scene`}
                            className="w-full rounded border border-purple-500/30"
                        />
                        <div className="absolute bottom-2 right-2">
                            <Button
                                variant="outline"
                                size="sm"
                                className="bg-black/70 text-xs"
                                onClick={() => {
                                    const link = document.createElement('a');
                                    link.href = sceneImage.startsWith('data:') ? sceneImage : `data:image/png;base64,${sceneImage}`;
                                    link.download = `${locationId}_tick${currentTick}.png`;
                                    link.click();
                                }}
                            >
                                📥 Download
                            </Button>
                        </div>
                    </div>
                )}

                {/* Style Info */}
                <div className="text-xs text-zinc-600 text-center">
                    Powered by Gemini 2.5 Flash • Signal Noir Style
                </div>
            </CardContent>
        </Card>
    );
}
