import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function Home() {
  return (
    <div className="container mx-auto max-w-5xl">
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-6">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900">
          零废标风险，<span className="text-primary">智能秒级拆解。</span>
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
          专为政企项目打造的智能标书助手。自动提取实质性响应要求、强制条款与商务要素，精准规避废标风险，一键生成原生排版 Word 框架。
        </p>
        <div className="flex gap-4 pt-6">
          <Link href="/analyze">
            <Button size="lg" className="rounded-full px-8 text-lg shadow-lg hover:shadow-xl transition-all">
              新建解析项目
            </Button>
          </Link>
          <Link href="/settings">
            <Button variant="outline" size="lg" className="rounded-full px-8 text-lg">
              配置底层大模型
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>1. 上传招标文件</CardTitle>
            <CardDescription>支持超长 PDF 与 Word 原件解析</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            多模态引擎自动剔除无关条款，聚焦「投标人须知」与「评标办法」。
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>2. “致命雷达”扫雷</CardTitle>
            <CardDescription>★ / ▲ 及实质性响应项一览</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            自动生成废标拦截清单，任何遗漏强制标红，确保100%投标合规。
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle>3. 原生 Word 组装</CardTitle>
            <CardDescription>资质、方案、克隆表格一键合并</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            不用手动画表，不使用纯文本转换。底层写入真正的 Microsoft Word 格式。
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
