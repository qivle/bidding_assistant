"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import Link from "next/link";

export default function HistoryPage() {
    const [projects, setProjects] = useState<any[]>([]);
    const [loadingId, setLoadingId] = useState<string | null>(null);

    useEffect(() => {
        fetch("http://localhost:8000/api/projects")
            .then(res => res.json())
            .then(data => setProjects(data.data || []))
            .catch(() => toast.error("无法加载历史项目"));
    }, []);

    const handleReGenerate = async (id: string) => {
        setLoadingId(id);
        try {
            // Fetch full analysis data
            const res = await fetch(`http://localhost:8000/api/projects/${id}`);
            if (!res.ok) throw new Error("无法读取项目详情");
            const data = await res.json();
            const analysisData = data.data.analysis_data;

            toast.info("正在重新组装 Word 标书...");
            
            const formData = new FormData();
            formData.append("data", JSON.stringify(analysisData));

            const genRes = await fetch("http://localhost:8000/api/generate", {
                method: "POST",
                body: formData,
            });

            if (!genRes.ok) throw new Error("生成失败");

            const blob = await genRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${analysisData.projectInfo?.name || '历史政企投标文件'}_恢复版.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            toast.success("标书已成功恢复下载！");
        } catch (err: any) {
            toast.error(err.message);
        } finally {
            setLoadingId(null);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">历史项目库</h1>
                    <p className="text-slate-500 mt-2">本地私有化保存的所有招标解析记录</p>
                </div>
                <Link href="/analyze">
                    <Button variant="outline">新建解析</Button>
                </Link>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.length === 0 ? (
                    <p className="text-slate-400">暂无保存的历史项目</p>
                ) : (
                    projects.map((p) => (
                        <Card key={p.id} className="flex flex-col">
                            <CardHeader>
                                <CardTitle className="text-lg line-clamp-2">{p.name || "未命名项目"}</CardTitle>
                                <CardDescription>编号: {p.number || "无"}</CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1 flex flex-col justify-end">
                                <p className="text-xs text-slate-400 mb-4">
                                    解析时间: {new Date(p.created_at).toLocaleString()}
                                </p>
                                <Button 
                                    className="w-full bg-blue-600 hover:bg-blue-700" 
                                    onClick={() => handleReGenerate(p.id)}
                                    disabled={loadingId === p.id}
                                >
                                    {loadingId === p.id ? "正在恢复..." : "重新生成 Word 框架"}
                                </Button>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>
        </div>
    );
}
