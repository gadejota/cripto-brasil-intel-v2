from __future__ import annotations

from datetime import datetime, timezone

from app.models import Article, EditorialPackage, MarketContext, ReelScript, Slide


def build_editorial_package(article: Article, context: MarketContext) -> EditorialPackage:
    direction = 'otimista' if article.sentiment == 'positivo' else 'defensivo' if article.sentiment == 'negativo' else 'equilibrado'
    price_anchor = f"BTC em US${context.btc_price_usd:,.0f}" if context.btc_price_usd else 'mercado sem preço atualizado no momento'
    hook = f"{article.title[:110]} — por que isso importa para quem investe em cripto no Brasil agora?"
    angle = (
        f"Ângulo {direction}: conectar o fato de {article.source_name} com impacto prático, "
        f"sem promessa de preço e sem copiar a notícia."
    )
    summary = (
        f"{article.why_it_matters} Contexto de mercado: {price_anchor}, Fear & Greed em "
        f"{context.fear_greed}/100 e dominância do BTC em {context.btc_dominance:.1f}%"
        if context.btc_dominance
        else article.why_it_matters
    )
    slides = [
        Slide(title='Gancho', body=hook, source=article.source_name),
        Slide(title='O que aconteceu', body=article.description or article.title, source=article.source_name),
        Slide(title='Por que importa', body=article.why_it_matters, source=article.source_name),
        Slide(title='Leitura de mercado', body=f'{price_anchor}. Sentimento do mercado: {context.fear_greed_label}.', source='Contexto de mercado'),
        Slide(title='Risco', body='Evite transformar manchete em certeza. Evento relevante não é sinônimo de trade óbvio.', source='Cripto Brasil Intel'),
        Slide(title='Conclusão', body='Salva esse carrossel. Não pela previsão. Pelo contexto.', source='Cripto Brasil Intel'),
    ]
    caption = (
        f"{hook}\n\n{summary}\n\n"
        '#bitcoin #criptomoedas #mercadocripto #economia #investimentos #criptonoticias'
    )
    reel = ReelScript(
        hook=hook,
        beats=[
            'Abre com a contradição central da notícia.',
            article.description or article.title,
            article.why_it_matters,
            f'Fecha com o contexto: Fear & Greed {context.fear_greed}/100.',
        ],
        close='Salva esse vídeo pelo contexto, não pela previsão.',
    )
    return EditorialPackage(
        article_id=article.id,
        hook=hook,
        angle=angle,
        summary=summary,
        caption=caption,
        call_to_action='Quer mais conteúdo assim? Aprova essa pauta na fila editorial.',
        slides=slides,
        reel=reel,
        prompt_image=(
            'Instagram editorial cover, brazilian crypto market, modern newsroom dashboard, '
            'high contrast typography, no logos, 4:5'
        ),
        generated_at=datetime.now(timezone.utc),
        mode='template',
    )
