# Importamos las librerías necesarias
from shiny import App, ui, reactive, render
from shinywidgets import output_widget, render_widget
import plotly.express as px
from data_prep import load_data, make_features, robust_thresholds
from pathlib import Path
import sys


# Definimos la ruta base del módulo para construir rutas relativas
HERE = Path(__file__).resolve().parent
WWW = HERE / "www"

# Definimos una paleta coherente para mantener consistencia visual entre vistas
PAL = {
    "blue":      "#224E7F",
    "edge":      "#385E88",
    "pink":      "#EC008C",
    "violet":    "#582156",
    "mag":       "#9A187D",
    "violet1":   "#3e1d3d",
    "pink2":     "#e92189",
}

# Cargamos el dataset una única vez y generamos las variables derivadas
df = make_features(load_data())

# Calculamos los umbrales robustos (p99.5) para acotar los ejes y mejorar la
# legibilidad sin depender de los máximos extremos
thr = robust_thresholds(df)

# Construimos la barra lateral con filtros globales que afectan a todas las
# pestañas
sidebar = ui.sidebar(
    ui.h4(
        "Filtros globales",
        style="margin-bottom:-10px;",
    ),
    ui.hr(
        style="margin-top:0px; margin-bottom:0px;",
    ),
    ui.input_slider(
        "recency",
        "Días desde la última compra",
        0,
        int(df["Recency"].max()),
        value=(0, 99),
    ),
    ui.input_slider(
        "income",
        "Rango de ingresos (Income)",
        0,
        int(thr["inc_p995"]),
        value=(0, int(thr["inc_p995"])),
    ),
    ui.input_select(
        "response",
        "Respuesta a la última campaña (Response)",
        choices=["Todas", "No aceptó (0)", "Aceptó (1)"],
        selected="Todas",
    ),
    ui.input_action_button(
        "reset",
        "Restablecer filtros",
        class_="btn-light",
    ),
    ui.hr(
        style="margin-top:0px; margin-bottom:0px;",
    ),
    ui.h5("Resumen del filtro"),
    ui.output_ui("kpi_text"),
    ui.help_text(
        ui.tags.span(
            ui.tags.span("Response: "),
            ui.tags.br(),
            ui.tags.span("1 = aceptó la última campaña."),
            ui.tags.br(),
            ui.tags.span("0 = no aceptó."),
            style="color:#ffffff;line-height:1.1;",
        )
    ),
    ui.help_text(
        ui.tags.span(
            "Los filtros se aplican a todas las páginas.",
            style="color:#ffffff;",
        )
    ),
    bg=PAL["edge"],
    fg="#ffffff",
)

# Definimos el encabezado de la aplicación
title_ui = ui.tags.div(
    ui.tags.img(
        src="logo.png",
        height="28",
        style="margin-right:10px; vertical-align:middle;",
    ),
    ui.tags.div(
        ui.tags.div(
            "Personality Analysis",
            style="font-weight:600; line-height:1.0;",
        ),
        ui.tags.div(
            "Explorador de respuesta a campañas comerciales",
            style="font-size:0.85rem; line-height:1.0; opacity:0.9;",
        ),
        style="display:inline-block; vertical-align:middle;",
    ),
)

# Definimos la navegación por pestañas y el contenido principal de la app
app_ui = ui.page_navbar(
    ui.nav_panel(
        "Contexto y preguntas",
        ui.h3("Contexto, preguntas y objetivos"),
        ui.h4("Descripción del conjunto de datos"),
        ui.output_text("facts_text"),
        ui.hr(),
        ui.h4("Variables clave"),
        ui.output_ui("vars_text"),
        ui.hr(),
        output_widget("fig_income"),
        ui.output_ui("income_note"),
        ui.hr(),
        ui.h4("Preguntas y objetivos"),
        ui.tags.ul(
            ui.tags.li(
                "¿Cómo varía Response según el gasto total y el número de "
                "días desde la última compra?"
            ),
            ui.tags.li(
                "¿Cómo difieren los canales entre Response = 0 y 1?"
            ),
            ui.tags.li(
                "¿Qué categorías de gasto distinguen ambos grupos?"
            ),
        ),
        ui.p(
            "Objetivo: identificar patrones y diferencias entre grupos a "
            "partir de los datos, interpretándolos como asociaciones "
            "descriptivas y no como efectos causales, y permitir la "
            "exploración interactiva mediante filtros."
        ),
        ui.hr(),
        ui.h4("Decisiones y limitaciones"),
        ui.p(
            "Los resultados se presentan de forma agregada para reducir "
            "riesgos de reidentificación. La muestra procede de un contexto "
            "empresarial específico (representatividad no garantizada) y la "
            "interpretación es descriptiva, sin inferir causalidad."
        ),
        ui.p(
            "El recorte visual p99.5 se emplea únicamente para mejorar "
            "la legibilidad y no elimina observaciones del conjunto de datos."
        ),
        ui.hr(),
        ui.h4("Uso de la visualización"),
        ui.p(
            "Los filtros globales modifican todas las vistas y permiten "
            "explorar cómo cambian los patrones por días desde la última "
            "compra, ingresos y su respuesta."
        ),
    ),
    ui.nav_panel(
        "Respuesta a campañas",
        ui.h3("Respuesta a campañas (Response)"),
        ui.output_ui("kpi_campaigns"),
        ui.hr(),
        ui.h5("Filtro de rango de gasto total"),
        ui.input_slider(
            "spend_range",
            "Rango de gasto total (TotalSpend)",
            0,
            int(df["TotalSpend"].max()),
            value=(0, int(df["TotalSpend"].max())),
        ),
        ui.layout_columns(
            output_widget("fig_spend_box"),
            output_widget("fig_channel_bar"),
            col_widths=(6, 6),
        ),
        ui.hr(),
        output_widget("fig_cats_bar"),
        output_widget("fig_recency_spend"),
    ),
    ui.nav_panel(
        "Patrones de compra",
        ui.h3("Patrones de compra: canales y estructura del gasto"),
        ui.p(
            "Las siguientes vistas describen la composición relativa de "
            "compras y gasto. La normalización a porcentaje facilita la "
            "comparación entre grupos, independientemente del nivel de gasto."
        ),
        ui.input_select(
            "seg_var",
            "Segmentación (opcional)",
            choices=[
                "Sin segmentación",
                "Nivel educativo",
                "Estado civil",
                "Menores en el hogar",
            ],
            selected="Sin segmentación",
        ),
        output_widget("fig_channel_mix"),
        ui.hr(),
        output_widget("fig_spend_mix"),
        ui.hr(),
        output_widget("fig_channel_heat"),
    ),
    ui.nav_panel(
        "Conclusiones",
        ui.h3("Conclusiones y aprendizajes"),
        ui.p(
            "Síntesis final basada en las vistas anteriores. El resumen se "
            "actualiza con los filtros globales."
        ),
        ui.h4("Resumen con filtros actuales"),
        ui.output_ui("concl_kpis"),
        ui.hr(),
        ui.h4("¿Qué he aprendido del conjunto de datos?"),
        ui.p(
            "El conjunto de datos combina variables sociodemográficas y "
            "comportamentales, lo que permite describir perfiles de compra y "
            "su relación con la aceptación de campañas. La distribución de "
            "ingresos y del gasto es asimétrica, por lo que conviene emplear "
            "medidas robustas y visualizaciones que controlen los valores "
            "extremos."
        ),
        ui.h4("¿Qué he aprendido de las visualizaciones propuestas?"),
        ui.p(
            "Las comparaciones por grupos (Response) son más interpretables "
            "al combinar una magnitud (como el gasto) con una estructura (mix "
            "de canales y categorías). La normalización a porcentajes "
            "facilita identificar patrones de composición sin confundirlos "
            "con el volumen total."
        ),
        ui.h4("¿Qué he aprendido durante el proceso de visualización?"),
        ui.p(
            "El diseño interactivo requiere equilibrar la expresividad y el"
            "rendimiento. Para ello se utilizan filtros globales, la "
            "segmentación y escalas adecuadas, que mejoran la exploración sin "
            "sobrecargar la interfaz. Además, la consistencia visual (la "
            "paleta de colores, la tipografía y la jerarquía) aumenta la "
            "claridad del relato y facilita la interpretación de los datos."
        ),
    ),
    title=title_ui,
    id="nav",
    sidebar=sidebar,
    navbar_options=ui.navbar_options(
        theme="dark",
        bg=PAL["pink2"],
    ),
)


# Definimos la lógica  del servidor: aquí aplicamos los filtros,
# calculamos los KPIs y generamos las figuras
def server(input, output, session):
    @reactive.calc
    # Construimos el DataFrame filtrado que actúa como fuente  para todas las
    # vistas y KPIs
    def df_f():
        # Aplicamos los filtros globales (recency e income) sobre el DataFrame
        r0, r1 = input.recency()
        i0, i1 = input.income()

        d = df[(df["Recency"] >= r0) & (df["Recency"] <= r1)]
        d = d[
            d["Income"].isna()
            | ((d["Income"] >= i0) & (d["Income"] <= i1))
        ]

        # Aplicamos el filtro específico de la pestaña “Respuesta a campañas”
        # (rango de gasto total)
        s0, s1 = input.spend_range()
        d = d[(d["TotalSpend"] >= s0) & (d["TotalSpend"] <= s1)]

        # Convertimos la selección de Response a una condición de filtrado
        # (si no es “Todas”)
        sel = input.response()

        if sel == "No aceptó (0)":
            d = d[d["Response"] == 0]

        if sel == "Aceptó (1)":
            d = d[d["Response"] == 1]

        return d

    @output
    @render.text
    # Generamos un resumen descriptivo del dataset (tamaño, missing de Income,
    # tasa base de Response y rango temporal)
    def facts_text():
        # Creamos un resumen básico del dataset para contextualizar la app
        n = len(df)
        inc_miss = 100.0 * float(df["Income"].isna().mean())
        resp = 100.0 * float(df["Response"].mean())
        dt0 = df["Dt_Customer"].min().date()
        dt1 = df["Dt_Customer"].max().date()
        return (
            f"Registros: {n}\n"
            f"Ingresos faltantes: {inc_miss:.2f}%\n"
            f"Response=1: {resp:.2f}%\n"
            f"Dt_Customer: {dt0} -> {dt1}"
        )

    @output
    @render.ui
    # Mostramos una definición de las variables para facilitar la
    # interpretación de las gráficas
    def vars_text():
        return ui.tags.dl(
            ui.tags.dt("Respuesta a la última campaña (Response)"),
            ui.tags.dd(
                "Indicador binario: 1 = aceptó la última campaña; "
                "0 = no aceptó."
            ),
            ui.tags.dt("Días desde la última compra (Recency)"),
            ui.tags.dd(
                "Tiempo transcurrido desde la última compra (en días)."
            ),
            ui.tags.dt("Total gastado (TotalSpend)"),
            ui.tags.dd(
                "Gasto total: suma de categorías Mnt* (vino, fruta, carne, "
                "pescado, dulces y oro)."
            ),
            style="margin-bottom:0;",
        )

    @output
    @render.ui
    # Añadimos una nota sobre Income
    def income_note():
        # Aclaramos que el p99.5 se usa como referencia visual y no como
        # eliminación de observaciones
        return ui.tags.p(
            "La distribución de ingresos (Income) se acompaña de referencias "
            "descriptivas (media, mediana y p99.5). El recorte visual p99.5 "
            "se utiliza únicamente para mejorar la legibilidad del eje, sin "
            "eliminar observaciones del conjunto de datos.",
            style="margin-top:0.5rem;",
        )

    @output
    @render_widget
    # Representamos la distribución de Income y añadimos las referencias
    # con los filtros activos
    def fig_income():
        d = df_f()

        # Visualizamos la distribución de Income con un histograma y líneas de
        # referencia para media, mediana y p99.5
        fig = px.histogram(
            d,
            x="Income",
            nbins=45,
            title="Distribución de Ingresos (Income)",
            color_discrete_sequence=[PAL["blue"]],
        )
        fig.update_traces(marker_line_color=PAL["edge"])

        inc = d["Income"].dropna()

        # Controlamos el caso sin valores para evitar errores y comunicarlo en
        # la propia figura
        if inc.empty:
            fig.add_annotation(
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                text="Sin valores de Ingresos (Income) con los filtros "
                     "actuales",
                showarrow=False,
            )
            return fig

        p995 = float(inc.quantile(0.995))
        mean = float(inc.mean())
        med = float(inc.median())

        # Añadimos las referencias (media, mediana y p99.5) a la figura
        fig.add_vline(x=mean, line_dash="dot",  line_color=PAL["pink2"])
        fig.add_vline(x=med,  line_dash="dash", line_color=PAL["violet"])
        fig.add_vline(x=p995, line_dash="dash", line_color=PAL["mag"])

        # Añadimos etiquetas con los valores numéricos correspondientes
        fig.add_annotation(
            x=mean,
            y=1.02,
            yref="paper",
            text=f"Media: {mean:,.0f}",
            showarrow=False,
            font=dict(color=PAL["pink2"]),
        )
        fig.add_annotation(
            x=med,
            y=1.08,
            yref="paper",
            text=f"Mediana: {med:,.0f}",
            showarrow=False,
            font=dict(color=PAL["violet"]),
        )
        fig.add_annotation(
            x=p995,
            y=1.07,
            yref="paper",
            text=f"p99.5: {p995:,.0f}",
            showarrow=False,
            font=dict(color=PAL["mag"]),
        )

        return fig

    @output
    @render.ui
    # Calculamos un resumen de la campaña con los filtros actuales (tasa
    # Response = 1 y la diferencia de mediana de gasto entre grupos)
    def kpi_campaigns():
        d = df_f()

        # Si el filtrado deja el conjunto vacío, lo reportamos explícitamente
        if d.empty:
            return ui.tags.p(
                "Sin datos con los filtros actuales.",
                style="margin:0;",
            )

        # Generamos un resumen general del tamaño de la muestra filtrado y la
        # tasa de aceptación de la última campaña
        n = int(len(d))
        rate = 100.0 * float(d["Response"].mean())

        # Comparamos el gasto total entre grupos mediante la mediana
        d0 = d.loc[d["Response"] == 0, "TotalSpend"].dropna()
        d1 = d.loc[d["Response"] == 1, "TotalSpend"].dropna()

        if d0.empty or d1.empty:
            txt = (
                f"Registros (filtrados): {n} | "
                f"Tasa Response = 1: {rate:.2f}% | "
                "Comparación de gasto: no disponible (falta un grupo)."
            )
            return ui.tags.p(txt, style="margin:0;")

        med0 = float(d0.median())
        med1 = float(d1.median())
        delta = med1 - med0

        # Mostramos el resumen calculado
        txt = (
            f"Registros (filtrados): {n} | "
            f"Tasa Response = 1: {rate:.2f}% | "
            f"Mediana TotalSpend (0): {med0:,.0f} | "
            f"Mediana TotalSpend (1): {med1:,.0f} | "
            f"Diferencia de gasto (1-0): {delta:,.0f}"
        )

        # Definimos el estilo básico del bloque de texto
        return ui.tags.p(
            txt,
            style=(
                "margin:0;"
                "padding:0.25rem 0.5rem;"
                "border-left:4px solid " + PAL["mag"] + ";"
                "background:rgba(0,0,0,0.03);"
            ),
        )

    @output
    @render_widget
    # Comparamos la distribución de TotalSpend entre Response = 0 y
    # Response = 1 mediante un boxplot
    def fig_spend_box():
        d = df_f()
        # Controlamos el caso sin datos para evitar figuras vacías
        if len(d) == 0:
            return px.scatter(title="Sin datos para los filtros actuales")

        d2 = d.copy()
        d2["Response_lbl"] = d2["Response"].map(
            {0: "Response = 0", 1: "Response = 1"}
        )

        # Comparamos la distribución de gasto por grupos con un boxplot
        fig = px.box(
            d2,
            x="Response_lbl",
            y="TotalSpend",
            points=False,
            title="Gasto total (TotalSpend) según Response",
            color="Response_lbl",
            color_discrete_map={
                "Response = 0": PAL["blue"],
                "Response = 1": PAL["mag"],
            },
        )
        fig.update_layout(showlegend=False)
        return fig

    @output
    @render_widget
    # Comparamos las compras medias por canal (web, catálogo, tienda) entre
    # grupos de Response
    def fig_channel_bar():
        try:
            d = df_f()
            if d.empty:
                return px.scatter(title="Sin datos para los filtros actuales")

            # Estimamos las compras medias por canal y por grupo para comparar
            # los comportamientos
            cols = ["NumWebPurchases", "NumCatalogPurchases",
                    "NumStorePurchases"]
            g = d[["Response"] + cols].groupby("Response").mean().reset_index()

            g_long = g.melt(
                id_vars="Response",
                value_vars=cols,
                var_name="Canal",
                value_name="Compras_medias",
            )

            # Renombramos los canales para mejorar la legibilidad del gráfico
            map_canal = {
                "NumWebPurchases": "Web",
                "NumCatalogPurchases": "Catálogo",
                "NumStorePurchases": "Tienda",
            }
            g_long["Canal"] = g_long["Canal"].map(map_canal)
            g_long["Response"] = g_long["Response"].map(
                {0: "Response = 0", 1: "Response = 1"}
            )

            # Definimos el gráfico
            fig = px.bar(
                g_long,
                x="Canal",
                y="Compras_medias",
                color="Response",
                barmode="group",
                title="Compras medias por canal según Response",
                color_discrete_map={
                    "Response = 0": PAL["blue"],
                    "Response = 1": PAL["mag"],
                },
            )
            return fig

        except Exception as e:
            # Reportamos errores en stderr para la depuración sin romper la app
            print(f"ERROR fig_channel_bar: {e}", file=sys.stderr)
            return px.scatter(title=f"Error en fig_channel_bar: {e}")

    @output
    @render_widget
    # Comparamos el gasto medio por categorías (Mnt*) entre los grupos Response
    def fig_cats_bar():
        try:
            d = df_f()
            if d.empty:
                return px.scatter(title="Sin datos para los filtros actuales")

            # Comparamos el gasto medio por categoría (Mnt*) entre Response = 0
            # y Response = 1
            cats = [
                "MntWines",
                "MntFruits",
                "MntMeatProducts",
                "MntFishProducts",
                "MntSweetProducts",
                "MntGoldProds",
            ]

            g = d[["Response"] + cats].groupby("Response").mean().reset_index()
            g_long = g.melt(
                id_vars="Response",
                value_vars=cats,
                var_name="Categoria",
                value_name="Gasto_medio",
            )

            # Renombramos las categorías para facilitar la lectura
            map_cat = {
                "MntWines": "Vino",
                "MntFruits": "Fruta",
                "MntMeatProducts": "Carne",
                "MntFishProducts": "Pescado",
                "MntSweetProducts": "Dulces",
                "MntGoldProds": "Oro",
            }
            g_long["Categoria"] = g_long["Categoria"].map(map_cat)
            g_long["Response"] = g_long["Response"].map(
                {0: "No aceptan", 1: "Aceptan"}
            )

            # Mostramos el gráfico
            fig = px.bar(
                g_long,
                x="Categoria",
                y="Gasto_medio",
                color="Response",
                barmode="group",
                title="Gasto medio por categoría según Response",
                color_discrete_map={
                    "No aceptan": PAL["blue"],
                    "Aceptan": PAL["mag"],
                },
            )
            return fig

        except Exception as e:
            print(f"ERROR fig_cats_bar: {e}", file=sys.stderr)
            return px.scatter(title=f"Error en fig_cats_bar: {e}")

    @output
    @render_widget
    # Analizamos la asociación entre Recency y TotalSpend por cada grupo de
    # Response
    def fig_recency_spend():
        d = df_f()
        if d.empty:
            return px.scatter(title="Sin datos para los filtros actuales")

        d2 = d.copy()
        d2["Response_lbl"] = d2["Response"].map(
            {0: "No aceptó", 1: "Aceptó"}
        )

        # Analizamos la asociación Recency – TotalSpend y usamos la escala log
        # en y para tratar asimetría del gasto
        fig = px.scatter(
            d2,
            x="Recency",
            y="TotalSpend",
            color="Response_lbl",
            opacity=0.6,
            title="Relación entre antigüedad de compra y gasto total "
                  "(por respuesta la última campaña)",
            labels={
                "Recency": "Días desde la última compra",
                "TotalSpend": "Gasto total",
                "Response_lbl": "Respuesta",
            },
            color_discrete_map={
                "No aceptó": PAL["blue"],
                "Aceptó": PAL["mag"],
            },
            log_y=True,
        )
        fig.update_traces(marker_line_color=PAL["edge"])
        return fig

    @reactive.calc
    # Traducimos la selección de la segmentación a la columna del dataset que
    # se usará para el mapeado
    def seg_col():
        sel = input.seg_var()

        mapping = {
            "Nivel educativo": "Education",
            "Estado civil": "Marital_Status",
            "Menores en el hogar": "ChildrenHome",
        }

        return mapping.get(sel)

    @output
    @render_widget
    # Calculamos el mix de canales como cuotas normalizadas y lo comparamos
    # por Response
    def fig_channel_mix():
        d = df_f()

        if d.empty:
            return px.scatter(title="Sin datos para los filtros actuales")

        cols = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
        d2 = d[["Response"] + cols].copy()

        # Calculamos el total por fila para obtener cuotas relativas por canal
        # y no depender del volumen completo de compras
        d2["TotCh"] = d2[cols].sum(axis=1)
        d2 = d2[d2["TotCh"] > 0].copy()

        if d2.empty:
            return px.scatter(title="Sin compras en los filtros actuales")

        d2["Response_lbl"] = d2["Response"].map({0: "No aceptó", 1: "Aceptó"})

        s = seg_col()
        if s is not None and s in d.columns:
            d2[s] = d.loc[d2.index, s].astype(str)
            group_cols = ["Response_lbl", s]
        else:
            group_cols = ["Response_lbl"]

        # Normalizamos la cuota por canal y promediamos las cuotas individuales
        # por grupo
        for c in cols:
            d2[c] = d2[c] / d2["TotCh"]

        g = d2.groupby(group_cols)[cols].mean().reset_index()

        g_long = g.melt(
            id_vars=group_cols,
            value_vars=cols,
            var_name="Canal",
            value_name="Cuota",
        )

        map_canal = {
            "NumWebPurchases": "Web",
            "NumCatalogPurchases": "Catálogo",
            "NumStorePurchases": "Tienda",
        }
        g_long["Canal"] = g_long["Canal"].map(map_canal)

        title = "Mix de canales (cuota media, normalizada)"
        if s is not None:
            title = f"Mix de canales (cuota media) por {s}"

        # Mostramos el gráfico
        fig = px.bar(
            g_long,
            x="Response_lbl",
            y="Cuota",
            color="Canal",
            barmode="stack",
            facet_col=s if s is not None else None,
            title=title,
            labels={"Response_lbl": "Respuesta", "Cuota": "Cuota"},
        )

        # Establecemos los márgenes para mejorar la legibilidad
        fig.update_layout(
            margin=dict(t=75, r=20, b=50, l=60),
            title=dict(
                y=0.98,
                yanchor="top",
                pad=dict(t=20, b=0),
            ),
        )

        fig.update_traces(marker_line_color=PAL["edge"])
        fig.update_yaxes(tickformat=".0%")
        return fig

    @output
    @render_widget
    # Calculamos la composición del gasto como cuotas por categoría y la
    # comparamos por Response
    def fig_spend_mix():
        d = df_f()

        if d.empty:
            return px.scatter(title="Sin datos para los filtros actuales")

        cats = [
            "MntWines",
            "MntFruits",
            "MntMeatProducts",
            "MntFishProducts",
            "MntSweetProducts",
            "MntGoldProds",
        ]

        d2 = d[["Response", "TotalSpend"] + cats].copy()
        d2 = d2[d2["TotalSpend"] > 0].copy()

        if d2.empty:
            return px.scatter(title="Sin gasto en los filtros actuales")

        d2["Response_lbl"] = d2["Response"].map({0: "No aceptó", 1: "Aceptó"})

        s = seg_col()
        if s is not None and s in d.columns:
            d2[s] = d[s].astype(str)
            group_cols = ["Response_lbl", s]
        else:
            group_cols = ["Response_lbl"]

        # Normalizamos promediamos las cuotas individuales por grupo
        for c in cats:
            d2[c] = d2[c] / d2["TotalSpend"]

        g = d2.groupby(group_cols)[cats].mean().reset_index()

        g_long = g.melt(
            id_vars=group_cols,
            value_vars=cats,
            var_name="Categoria",
            value_name="Cuota",
        )

        map_cat = {
            "MntWines": "Vino",
            "MntFruits": "Fruta",
            "MntMeatProducts": "Carne",
            "MntFishProducts": "Pescado",
            "MntSweetProducts": "Dulces",
            "MntGoldProds": "Oro",
        }
        g_long["Categoria"] = g_long["Categoria"].map(map_cat)

        title = "Composición del gasto (cuota media, normalizada)"
        if s is not None:
            title = f"Composición del gasto (cuota media) por {s}"

        # Mostramos el gráfico
        fig = px.bar(
            g_long,
            x="Response_lbl",
            y="Cuota",
            color="Categoria",
            barmode="stack",
            facet_col=s if s is not None else None,
            title=title,
            labels={"Response_lbl": "Respuesta", "Cuota": "Cuota"},
        )

        fig.update_layout(
            margin=dict(t=75, r=20, b=50, l=60),
            title=dict(
                y=0.98,
                yanchor="top",
                pad=dict(t=20, b=0),
            ),
        )

        fig.update_traces(marker_line_color=PAL["edge"])
        fig.update_yaxes(tickformat=".0%")
        return fig

    @output
    @render_widget
    # Visualizamos la intensidad media de compra por canal y Response con un
    # mapa de calor
    def fig_channel_heat():
        d = df_f()

        if d.empty:
            return px.scatter(title="Sin datos para los filtros actuales")

        cols = ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"]
        d2 = d[["Response"] + cols].copy()
        d2["Response_lbl"] = d2["Response"].map({0: "No aceptó", 1: "Aceptó"})

        s = seg_col()
        if s is not None and s in d.columns:
            d2[s] = d[s].astype(str)
            group_cols = ["Response_lbl", s]
        else:
            group_cols = ["Response_lbl"]

        # Estimamos la intensidad media por canal y grupo para visualizarla
        # como mapa de calor
        g = d2.groupby(group_cols)[cols].mean().reset_index()

        g_long = g.melt(
            id_vars=group_cols,
            value_vars=cols,
            var_name="Canal",
            value_name="Compras_medias",
        )

        map_canal = {
            "NumWebPurchases": "Web",
            "NumCatalogPurchases": "Catálogo",
            "NumStorePurchases": "Tienda",
        }
        g_long["Canal"] = g_long["Canal"].map(map_canal)

        title = "Intensidad de compra por canal (media)"
        if s is not None:
            title = f"Intensidad de compra por canal (media) por {s}"

        # Mostramos el gráfico
        fig = px.density_heatmap(
            g_long,
            x="Canal",
            y="Response_lbl",
            z="Compras_medias",
            facet_col=s if s is not None else None,
            title=title,
            labels={"Response_lbl": "Respuesta"},
        )

        fig.update_layout(
            margin=dict(t=75, r=20, b=50, l=60),
            title=dict(y=0.98, yanchor="top", pad=dict(t=20)),
        )
        return fig

    @output
    @render.text
    # Mostramos en la barra lateral un KPI del filtrado (n y tasa Response=1)
    # para orientar la exploración
    def kpi_text():
        d = df_f()
        n = len(d)

        # Mostramos un resumen del filtrado en la barra lateral
        if n == 0:
            txt = "Registros = 0\nResponse =1: —"
        else:
            rate = 100.0 * float(d["Response"].mean())
            txt = f"Registros = {n}\nResponse = 1: {rate:.2f}%"

        return ui.tags.pre(
            txt,
            style=(
                "margin:0;"
                "padding:0;"
                "border:0;"
                "background:transparent;"
                "color:#ffffff;"
                "white-space:pre-line;"
                "font-family:inherit;"
                "font-size:0.95rem;"
            ),
        )

    @reactive.effect
    @reactive.event(input.reset)
    # Restablecemos los filtros globales a su configuración inicial
    def _reset_filters():
        ui.update_slider("recency", value=(0, 99))
        ui.update_slider(
            "income",
            value=(0, int(thr["inc_p995"])),
        )
        ui.update_select("response", selected="Todas")

    @output
    @render.ui
    # Generamos el resumen final con los filtros activos
    def concl_kpis():
        d = df_f()

        # Calculamos de nuevo un resumen final con los filtros activos
        if d.empty:
            return ui.tags.p("Sin datos con los filtros actuales.",
                             style="margin:0;")

        n = int(len(d))
        rate = 100.0 * float(d["Response"].mean())

        d0 = d.loc[d["Response"] == 0, "TotalSpend"].dropna()
        d1 = d.loc[d["Response"] == 1, "TotalSpend"].dropna()

        if d0.empty or d1.empty:
            txt = (
                f"Registros: {n} | "
                f"Tasa Response=1: {rate:.2f}% | "
                "Medianas de gasto: no disponibles (falta un grupo)."
            )
            return ui.tags.p(txt, style="margin:0;")

        med0 = float(d0.median())
        med1 = float(d1.median())
        delta = med1 - med0

        txt = (
            f"Registros: {n} | "
            f"Tasa Response=1: {rate:.2f}% | "
            f"Mediana TotalSpend (No aceptó): {med0:,.0f} | "
            f"Mediana TotalSpend (Aceptó): {med1:,.0f} | "
            f"Diferencia: {delta:,.0f}"
        )

        return ui.tags.p(
            txt,
            style=(
                "margin:0;"
                "padding:0.4rem 0.6rem;"
                "border-left:4px solid " + PAL["mag"] + ";"
                "background:rgba(0,0,0,0.03);"
            ),
        )


# Construimos la app e indicamos la carpeta de estáticos para mostrar el logo
app = App(app_ui, server, static_assets=str(WWW))
