# daily_app.py - Refatorado com navegação por telas e correções
import streamlit as st
from datetime import datetime
import json
import os

# Caminhos dos arquivos
CAMINHO_USUARIOS = "usuarios.json"
CAMINHO_IDS = "controle_ids.json"
PASTA_DAILIES = "dailies"
os.makedirs(PASTA_DAILIES, exist_ok=True)

# Utilitários

def carregar_usuarios():
    if os.path.exists(CAMINHO_USUARIOS):
        with open(CAMINHO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_usuarios(usuarios):
    with open(CAMINHO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)

def carregar_ids():
    if os.path.exists(CAMINHO_IDS):
        try:
            with open(CAMINHO_IDS, "r", encoding="utf-8") as f:
                ids = json.load(f)
            if not all(k in ids for k in ["usuarios", "atividades", "impedimentos"]):
                raise ValueError("IDs incompletos")
            return ids
        except:
            pass
    return {"atividades": {}, "impedimentos": {}, "usuarios": 1}

def salvar_ids(ids):
    with open(CAMINHO_IDS, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=4)

def gerar_id(tipo, data=None):
    ids = carregar_ids()
    if tipo == "usuario":
        novo_id = f"USR{ids['usuarios']:04d}"
        ids['usuarios'] += 1
    elif tipo == "atividade":
        chave = data or datetime.now().strftime("%Y-%m-%d")
        if chave not in ids['atividades']:
            ids['atividades'][chave] = 1
        novo_id = f"{chave}_{ids['atividades'][chave]:04d}"
        ids['atividades'][chave] += 1
    elif tipo == "impedimento":
        chave = data or datetime.now().strftime("%Y-%m-%d")
        if chave not in ids['impedimentos']:
            ids['impedimentos'][chave] = 1
        novo_id = f"{chave}_I{ids['impedimentos'][chave]:03d}"
        ids['impedimentos'][chave] += 1
    salvar_ids(ids)
    return novo_id

def carregar_dailies(mes_ano):
    caminho = os.path.join(PASTA_DAILIES, f"daily_{mes_ano}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_dailies(mes_ano, dailies):
    caminho = os.path.join(PASTA_DAILIES, f"daily_{mes_ano}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dailies, f, ensure_ascii=False, indent=4)

# Interfaces de tela

def tela_login():
    st.subheader("Selecione ou cadastre um usuário")
    usuarios = carregar_usuarios()
    nomes_usuarios = [u['nome'] for u in usuarios]
    opcao = st.radio("Você já possui cadastro?", ["Sim", "Não"])

    if opcao == "Sim":
        if nomes_usuarios:
            nome_selecionado = st.selectbox("Selecione seu nome", nomes_usuarios)
            if st.button("Entrar"):
                usuario_logado = next((u for u in usuarios if u['nome'] == nome_selecionado), None)
                st.session_state.usuario = usuario_logado
                st.session_state.menu = "principal"
                st.success(f"Bem-vindo(a), {usuario_logado['nome']}!")
        else:
            st.info("Nenhum usuário cadastrado ainda. Por favor, cadastre-se primeiro.")
    elif opcao == "Não":
        nome = st.text_input("Nome completo")
        email = st.text_input("Email")
        if st.button("Cadastrar"):
            if nome and email:
                novo_id = gerar_id("usuario")
                novo_usuario = {"id": novo_id, "nome": nome, "email": email}
                usuarios.append(novo_usuario)
                salvar_usuarios(usuarios)
                st.session_state.usuario = novo_usuario
                st.session_state.menu = "principal"
                st.success(f"Usuário {nome} cadastrado com sucesso!")
            else:
                st.warning("Preencha todos os campos para se cadastrar.")

def menu_principal():
    st.markdown(f"**Usuário logado:** {st.session_state.usuario['nome']} ({st.session_state.usuario['email']})")
    st.success("Escolha o que deseja fazer abaixo:")
    st.header("Menu Principal")

    if st.button("Consultar Atividades"):
        st.session_state.menu = "consultar_atividades"
    if st.button("Consultar Daily"):
        st.session_state.menu = "consultar_daily"
    if st.button("Adicionar Atividade"):
        st.session_state.menu = "adicionar_atividade"
    if st.button("Cadastrar Tarefa Planejada"):
        st.session_state.menu = "cadastrar_planejada"
    if st.button("Cadastrar Impedimento"):
        st.session_state.menu = "cadastrar_impedimento"
    if st.button("Gerar Texto Base (última daily)"):
        st.session_state.menu = "gerar_texto_base"
    if st.button("Exportar JSON (última daily)"):
        st.session_state.menu = "exportar_json"
    if st.button("Encerrar Turno"):
        st.session_state.menu = "encerrar_turno"

# Renderização da tela
st.title("DreamMakerProjetos - Gerador de Daily")
if "usuario" not in st.session_state:
    tela_login()
elif st.session_state.get("menu") == "principal":
    menu_principal()
elif st.session_state.get("menu") == "cadastrar_planejada":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_planejada"):
        st.session_state.menu = "principal"
    st.header("Cadastrar Tarefa Planejada")
    if "planejada_salva" not in st.session_state:
        st.session_state.planejada_salva = False

    if not st.session_state.planejada_salva:
        with st.form("form_planejada"):
            descricao = st.text_input("Descrição da tarefa planejada")
            prioridade = st.selectbox("Prioridade", ["baixa", "média", "alta"], index=1)
            categoria = st.text_input("Categoria (opcional)")
            tags = st.text_input("Tags (separadas por vírgula)")
            submitted = st.form_submit_button("Salvar Planejada")

        if st.button("Cancelar e Voltar ao Menu", key="cancelar_planejada"):
            st.session_state.menu = "principal"

        planejadas_salvas = st.session_state.get("planejadas_temp", [])
        if planejadas_salvas:
            st.subheader("Tarefas planejadas até o momento:")
            for pl in planejadas_salvas:
                st.markdown(f"- **{pl['descricao']}** | Prioridade: {pl['prioridade']} | Categoria: {pl.get('categoria', '-')}")

        if submitted:
            if descricao:
                data_hoje = datetime.now().strftime("%Y-%m-%d")
                id_planejada = gerar_id("atividade", data_hoje)
                planejada = {
                    "id": id_planejada,
                    "descricao": descricao,
                    "prioridade": prioridade,
                    "categoria": categoria or None,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()]
                }
                if planejada not in st.session_state.get("planejadas_temp", []):
                    st.session_state.setdefault("planejadas_temp", []).append(planejada)
                    st.session_state.planejada_salva = True
            else:
                st.warning("A descrição é obrigatória.")
    else:
        st.success("Tarefa planejada salva com sucesso!")
        st.info("Sua tarefa foi salva com sucesso. Você pode voltar ao menu.")
        if st.button("OK - Voltar ao Menu", key="ok_planejada"):
            st.session_state.planejada_salva = False
            st.session_state.menu = "principal"

elif st.session_state.get("menu") == "cadastrar_impedimento":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_impedimento"):
        st.session_state.menu = "principal"
    st.header("Cadastrar Impedimento")
    if "impedimento_salvo" not in st.session_state:
        st.session_state.impedimento_salvo = False

    if not st.session_state.impedimento_salvo:
        with st.form("form_impedimento"):
            descricao = st.text_input("Descrição do impedimento")
            relacionado = st.checkbox("Está relacionado a uma atividade?")
            id_relacionado = ""
            if relacionado:
                atividades = st.session_state.get("atividades_temp", [])
                opcoes = {f"{a['id']} - {a['descricao']}": a['id'] for a in atividades}
                id_relacionado = st.selectbox("Escolha a atividade relacionada", list(opcoes.keys()), key="atividade_relacionada") if opcoes else ""
                if id_relacionado:
                    id_relacionado = opcoes.get(id_relacionado, id_relacionado)
            submitted = st.form_submit_button("Salvar Impedimento")

        if st.button("Cancelar e Voltar ao Menu", key="cancelar_impedimento"):
            st.session_state.menu = "principal"

        impedimentos_salvos = st.session_state.get("impedimentos_temp", [])
        if impedimentos_salvos:
            st.subheader("Impedimentos até o momento:")
            for imp in impedimentos_salvos:
                rel = imp['id_relacionado'] if imp['relacionado'] else "-"
                st.markdown(f"- **{imp['descricao']}** | Relacionado a: {rel}")

        if submitted:
            if descricao:
                data_hoje = datetime.now().strftime("%Y-%m-%d")
                id_impedimento = gerar_id("impedimento", data_hoje)
                impedimento = {
                    "id": id_impedimento,
                    "descricao": descricao,
                    "relacionado": relacionado,
                    "id_relacionado": id_relacionado if relacionado else None
                }
                if impedimento not in st.session_state.get("impedimentos_temp", []):
                    st.session_state.setdefault("impedimentos_temp", []).append(impedimento)
                    st.session_state.impedimento_salvo = True
            else:
                st.warning("A descrição é obrigatória.")
    else:
        st.success("Impedimento salvo com sucesso!")
        st.info("Seu impedimento foi salvo com sucesso. Você pode voltar ao menu.")
        if st.button("OK - Voltar ao Menu", key="ok_impedimento"):
            st.session_state.impedimento_salvo = False
            st.session_state.menu = "principal"

elif st.session_state.get("menu") == "encerrar_turno":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_encerrar"):
        st.session_state.menu = "principal"

    st.header("Encerramento do Turno")
    data_referencia = st.date_input("Informe a data da Daily", datetime.today()).strftime("%Y-%m-%d")
    st.subheader(f"Registro de informações da Daily do dia {data_referencia}")

    atividades = st.session_state.get("atividades_temp", [])
    planejadas = st.session_state.get("planejadas_temp", [])
    impedimentos = st.session_state.get("impedimentos_temp", [])

    concluido_ids = []
    levar_hoje_ids = []

    if atividades:
        st.markdown("### Marque o status das atividades registradas:")
    for atv in atividades:
        cols = st.columns([3, 1, 1])
        cols[0].markdown(f"**{atv['descricao']}**")
        concluido = cols[1].checkbox("Concluída", key=f"concluida_{atv['id']}")
        levar = cols[2].checkbox("Levar para amanhã", key=f"levar_{atv['id']}")
        if concluido:
            concluido_ids.append(atv['id'])
        if levar:
            levar_hoje_ids.append(atv['id'])

    st.markdown("### Atividades registradas até o momento:")
    for atv in atividades:
        st.markdown(f"- **{atv['descricao']}** | Prioridade: {atv['prioridade']} | Categoria: {atv.get('categoria', '-')}")

    st.markdown("### Deseja adicionar mais tarefas planejadas para amanhã?")
    nova_planejada = st.text_input("Descrição da nova tarefa planejada")
    add_planejada = st.button("Adicionar Tarefa Planejada", key="add_nova_planejada")
    if add_planejada and nova_planejada:
        nova = {
            "id": gerar_id("atividade", data_referencia),
            "descricao": nova_planejada,
            "prioridade": "média",
            "categoria": None,
            "tags": []
        }
        st.session_state.setdefault("planejadas_temp", []).append(nova)
        st.success("Tarefa planejada adicionada!")

        if planejadas:
            st.markdown("### Tarefas planejadas até o momento:")
            for pl in planejadas:
                st.markdown(f"- **{pl['descricao']}** | Prioridade: {pl['prioridade']} | Categoria: {pl.get('categoria', '-')}")

    st.markdown("### Deseja adicionar mais impedimentos?")
    novo_imp = st.text_input("Descrição do novo impedimento")
    add_imp = st.button("Adicionar Impedimento", key="add_novo_imp")
    if add_imp and novo_imp:
        novo = {
            "id": gerar_id("impedimento", data_referencia),
            "descricao": novo_imp,
            "relacionado": False,
            "id_relacionado": None
        }
        st.session_state.setdefault("impedimentos_temp", []).append(novo)
        st.success("Impedimento adicionado!")

        if impedimentos:
            st.markdown("### Impedimentos registrados até o momento:")
            for imp in impedimentos:
                rel = imp['id_relacionado'] if imp['relacionado'] else "-"
                st.markdown(f"- **{imp['descricao']}** | Relacionado a: {rel}")

    if st.button("Finalizar Turno", key="finalizar_turno"):
        for atv in atividades:
            atv['concluida'] = atv['id'] in concluido_ids
            atv['levar_para_hoje'] = atv['id'] in levar_hoje_ids

        daily = {
            "id": f"{data_referencia}_{st.session_state.usuario['id']}",
            "data": data_referencia,
            "foi_realizada": True,
            "observacao": None,
            "usuario": {
                "id_usuario": st.session_state.usuario['id'],
                "nome": st.session_state.usuario['nome'],
                "email": st.session_state.usuario['email']
            },
            "atividades": atividades,
            "planejadas": planejadas,
            "impedimentos": impedimentos
        }

        ano_mes = data_referencia[:7].replace("-", "_")
        todas_dailies = carregar_dailies(ano_mes)
        todas_dailies.append(daily)
        salvar_dailies(ano_mes, todas_dailies)

        st.success(f"Daily do dia {data_referencia} finalizada e salva com sucesso!")

        st.session_state["atividades_temp"] = []
        st.session_state["planejadas_temp"] = []
        st.session_state["impedimentos_temp"] = []
        st.session_state.menu = "principal"


elif st.session_state.get("menu") == "consultar_daily":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_consulta_daily"):
        st.session_state.menu = "principal"
    st.header("Consultar Daily")

    data = st.date_input("Selecione a data para consultar a Daily")
    data_str = data.strftime("%Y-%m-%d")
    ano_mes = data.strftime("%Y_%m")

    dailies = carregar_dailies(ano_mes)
    encontrada = next((d for d in dailies if d["data"] == data_str and d["usuario"]["id_usuario"] == st.session_state.usuario["id"]), None)

    if encontrada:
        st.success("Daily encontrada!")
        st.json(encontrada)
        if st.button("Exportar Texto Base", key="exportar_texto_base"):
            texto = f"📅 Daily – {data_str}\n\n"
            texto += "✅ Ontem:\n\n"
            for a in encontrada["atividades"]:
                if a["concluida"]:
                    texto += f"• {a['descricao']}, Concluída.\n\n"
                else:
                    tag_imp = "Impedimento" if any(i['id_relacionado'] == a['id'] for i in encontrada['impedimentos']) else "Sem impedimento"
                    tag_hoje = "Será efetuada hoje" if a['levar_para_hoje'] else ""
                    info = ", ".join(filter(None, ["Pendente", tag_hoje, tag_imp]))
                    texto += f"• {a['descricao']}, {info}."

            texto += "📌 Hoje:\n\n"
            for p in encontrada["planejadas"]:
                tags = ", ".join(p["tags"]) if p["tags"] else ""
                texto += f"• {p['descricao']}, {p['prioridade']}, {p.get('categoria','')}, {tags}.\n"

            texto += "\n\n⚠️ Impedimentos:\n\n"
            if encontrada["impedimentos"]:
                for i in encontrada["impedimentos"]:
                    if i['relacionado'] and i['id_relacionado']:
                        texto += f"• {i['descricao']}, relacionada à atividade {i['id_relacionado']}.\n"
                    else:
                        texto += f"• {i['descricao']}, não está relacionada a nenhuma atividade.\n"
            else:
                texto += "• Nenhum impedimento registrado."

            st.text_area("Texto gerado:", texto, height=400)

        if st.button("Exportar JSON", key="exportar_json_consulta"):
            nome_arquivo = f"daily_{data_str}_{st.session_state.usuario['id']}.json"
            st.download_button("Clique para baixar", data=json.dumps(encontrada, ensure_ascii=False, indent=4), file_name=nome_arquivo, mime="application/json")
    else:
        st.warning("Nenhuma daily encontrada para essa data.")


elif st.session_state.get("menu") == "consultar_atividades":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_consulta_atividade"):
        st.session_state.menu = "principal"
    st.header("Consultar Atividades")

    atividades = st.session_state.get("atividades_temp", [])
    opcoes = [f"{a['id']} - {a['descricao']}" for a in atividades]
    selecionada = st.selectbox("Busque pela atividade cadastrada", opcoes) if opcoes else None

    if selecionada:
        id_selecionado = selecionada.split(" - ")[0]
        resultado = next((a for a in atividades if a['id'] == id_selecionado), None)
        if resultado:
            st.success("Atividade encontrada!")
            st.json(resultado)

    if atividades:
        st.markdown("### Todas as atividades registradas nesta sessão:")
        for atv in atividades:
            st.markdown(f"- **{atv['id']}** | {atv['descricao']} | Prioridade: {atv['prioridade']} | Categoria: {atv.get('categoria', '-')}")

elif st.session_state.get("menu") == "adicionar_atividade":
    if st.button("⬅️ Voltar ao Menu Principal", key="voltar_adicionar_atividade"):
        st.session_state.menu = "principal"
    st.header("Adicionar Nova Atividade")
    if "atividade_salva" not in st.session_state:
        st.session_state.atividade_salva = False

    if not st.session_state.atividade_salva:
        with st.form("form_atividade"):
            descricao = st.text_input("Descrição da atividade")
            prioridade = st.selectbox("Prioridade", ["baixa", "média", "alta"], index=1)
            categoria = st.text_input("Categoria (opcional)")
            tags = st.text_input("Tags (separadas por vírgula)")
            justificativa = st.text_area("Justificativa (opcional)")
            submitted = st.form_submit_button("Salvar Atividade")

        if st.button("Cancelar e Voltar ao Menu", key="cancelar_adicionar_atividade"):
            st.session_state.menu = "principal"

        # Exibir atividades já adicionadas
        atividades_salvas = st.session_state.get("atividades_temp", [])
        if atividades_salvas:
            st.subheader("Atividades salvas até o momento:")
            for atv in atividades_salvas:
                st.markdown(f"- **{atv['descricao']}** | Prioridade: {atv['prioridade']} | Categoria: {atv.get('categoria', '-')}")

        if submitted:
            if descricao:
                data_hoje = datetime.now().strftime("%Y-%m-%d")
                id_atividade = gerar_id("atividade", data_hoje)
                atividade = {
                    "id": id_atividade,
                    "descricao": descricao,
                    "concluida": False,
                    "levar_para_hoje": False,
                    "justificativa": justificativa or None,
                    "prioridade": prioridade,
                    "categoria": categoria or None,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()]
                }
                if atividade not in st.session_state.get("atividades_temp", []):
                    st.session_state.setdefault("atividades_temp", []).append(atividade)
                    st.session_state.atividade_salva = True
            else:
                st.warning("A descrição da atividade é obrigatória.")
    else:
        st.success("Atividade salva com sucesso!")
        st.info("Sua atividade foi salva com sucesso. Você pode voltar ao menu.")
        if st.button("OK - Voltar ao Menu", key="ok_adicionar_atividade"):
            st.session_state.atividade_salva = False
            st.session_state.menu = "principal"
