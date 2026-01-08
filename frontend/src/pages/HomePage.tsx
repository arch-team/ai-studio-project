import {
  Container,
  Header,
  SpaceBetween,
  Cards,
  Link,
  Box,
} from '@cloudscape-design/components';

const features = [
  {
    name: '训练任务管理',
    description: '创建、管理和监控分布式训练任务，支持 PyTorch DDP/FSDP/DeepSpeed。',
    href: '/training/jobs',
  },
  {
    name: '数据集管理',
    description: '上传和管理训练数据集，支持大文件断点续传。',
    href: '/datasets',
  },
  {
    name: '资源配额',
    description: '查看和管理团队 GPU 资源配额，优化资源利用率。',
    href: '/resources/quotas',
  },
  {
    name: '集群监控',
    description: '实时监控集群状态、GPU 利用率和训练进度。',
    href: '/resources/monitoring',
  },
  {
    name: '在线开发环境',
    description: '使用 JupyterLab 或 VS Code 进行在线模型开发和调试。',
    href: '/spaces',
  },
];

function HomePage() {
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header variant="h1" description="企业级 AI 模型训练和管理平台">
            欢迎使用 AI 训练平台
          </Header>
        }
      >
        <Box variant="p">
          本平台基于 AWS SageMaker HyperPod 构建，提供高效的分布式训练、
          智能资源调度和全生命周期模型管理能力。
        </Box>
      </Container>

      <Cards
        cardDefinition={{
          header: (item) => <Link href={item.href}>{item.name}</Link>,
          sections: [
            {
              id: 'description',
              content: (item) => item.description,
            },
          ],
        }}
        items={features}
        header={<Header>功能概览</Header>}
        cardsPerRow={[{ cards: 1 }, { minWidth: 500, cards: 2 }, { minWidth: 800, cards: 3 }]}
      />
    </SpaceBetween>
  );
}

export default HomePage;
