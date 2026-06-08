import re
import sys
import pygame
import time
import os
import random
import ctypes

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

PADROES_TOKEN = [
    ('INFINITO', r'\bINFINITO\b'),
    ('AVANCA', r'\bAVANCA\b'),
    ('RECUA', r'\bRECUA\b'),
    ('ESQUERDA', r'\bESQUERDA\b'),
    ('DIREITA', r'\bDIREITA\b'),
    ('DETECTA', r'\bDETECTA\b'),
    ('EXPLORAR', r'\bEXPLORAR\b'),
    ('REPITA', r'\bREPITA\b'),
    ('ENQUANTO', r'\bENQUANTO\b'),
    ('NAO', r'\bNAO\b'),
    ('SE', r'\bSE\b'),
    ('SENAO', r'\bSENAO\b'),
    ('OBSTACULO', r'\bOBSTACULO\b'),
    ('ENTAO', r'\bENTAO\b'),
    ('IGUAL', r'='),
    ('NUMERO', r'\d+'),
    ('CHAVE_ESQ', r'\{'),
    ('CHAVE_DIR', r'\}'),
    ('ESPACO', r'[ \t]+'),
    ('NOVALINHA', r'\n'),
]

class ErroSintaxe(Exception):
    def __init__(self, msg, linha):
        super().__init__(msg)
        self.msg = msg
        self.linha = linha

def lexer(codigo_fonte):
    regex_completa = '|'.join(f'(?P<{nome}>{padrao})' for nome, padrao in PADROES_TOKEN)
    tokens = []
    linha = 1
    pos_atual = 0
    for match in re.finditer(regex_completa, codigo_fonte):
        if match.start() > pos_atual:
            trecho_invalido = codigo_fonte[pos_atual:match.start()].strip()
            if trecho_invalido:
                palavra = trecho_invalido.split()[0]
                raise ErroSintaxe(f"Comando ou símbolo '{palavra}' não reconhecido na linha {linha}.", linha)
        tipo = match.lastgroup
        valor = match.group(tipo)
        if tipo == 'NOVALINHA':
            linha += 1
        elif tipo != 'ESPACO':
            tokens.append({'tipo': tipo, 'valor': valor, 'linha': linha})
        pos_atual = match.end()
    if pos_atual < len(codigo_fonte):
        trecho_invalido = codigo_fonte[pos_atual:].strip()
        if trecho_invalido:
            palavra = trecho_invalido.split()[0]
            raise ErroSintaxe(f"Comando '{palavra}' não reconhecido na linha {linha}.", linha)
    return tokens

class NoComando:
    def __init__(self, acao, valor=1):
        self.acao = acao
        self.valor = valor

class NoRepeat:
    def __init__(self, repeticoes, comandos):
        self.repeticoes = repeticoes
        self.comandos = comandos

class NoIfObstacle:
    def __init__(self, comando_then):
        self.comando_then = comando_then

class NoIfBlock:
    def __init__(self, comandos_then, comandos_else):
        self.comandos_then = comandos_then
        self.comandos_else = comandos_else

class NoWhileNotObstacle:
    def __init__(self, comandos):
        self.comandos = comandos

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicao = 0

    def token_atual(self):
        if self.posicao < len(self.tokens):
            return self.tokens[self.posicao]
        return None

    def consumir(self, tipo_esperado):
        token = self.token_atual()
        if token and token['tipo'] == tipo_esperado:
            self.posicao += 1
            return token
        if token:
            raise ErroSintaxe(f"Erro de sintaxe próximo a '{token['valor']}' na linha {token['linha']}.", token['linha'])
        raise ErroSintaxe("Fim de código inesperado. Algum bloco não foi fechado.", -1)

    def parse(self):
        infinito_ativo = False
        token_inicial = self.token_atual()
        if token_inicial and token_inicial['tipo'] == 'INFINITO':
            infinito_ativo = True
            self.posicao += 1
        comandos = []
        while self.posicao < len(self.tokens):
            comandos.append(self.parse_comando())
        return infinito_ativo, comandos

    def parse_comando(self):
        token = self.token_atual()
        if not token: raise ErroSintaxe("Fim de código inesperado.", -1)
        
        if token['tipo'] in ['AVANCA', 'RECUA']:
            acao = token['tipo']
            self.posicao += 1
            self.consumir('IGUAL')
            num_token = self.consumir('NUMERO')
            valor = int(num_token['valor'])
            if valor > 5000:
                raise ErroSintaxe(f"O limite maximo e 5000. Valor informado: {valor}", num_token['linha'])
            return NoComando(acao, valor)
        elif token['tipo'] in ['ESQUERDA', 'DIREITA']:
            acao = token['tipo']
            self.posicao += 1
            valor = 1
            if self.token_atual() and self.token_atual()['tipo'] == 'IGUAL':
                self.consumir('IGUAL')
                num_token = self.consumir('NUMERO')
                valor = int(num_token['valor'])
                if valor > 5000:
                    raise ErroSintaxe(f"O limite maximo e 5000. Valor informado: {valor}", num_token['linha'])
            return NoComando(acao, valor)
        elif token['tipo'] in ['DETECTA', 'EXPLORAR']:
            acao = token['tipo']
            self.posicao += 1
            return NoComando(acao)
        elif token['tipo'] == 'REPITA':
            self.posicao += 1
            repeticoes = -1
            if self.token_atual() and self.token_atual()['tipo'] == 'IGUAL':
                self.consumir('IGUAL')
                num_token = self.consumir('NUMERO')
                repeticoes = int(num_token['valor'])
                if repeticoes > 5000:
                    raise ErroSintaxe(f"O limite maximo de iteracoes e 5000. Valor informado: {repeticoes}", num_token['linha'])
            self.consumir('CHAVE_ESQ')
            comandos_internos = []
            while self.token_atual() and self.token_atual()['tipo'] != 'CHAVE_DIR':
                comandos_internos.append(self.parse_comando())
            self.consumir('CHAVE_DIR')
            return NoRepeat(repeticoes, comandos_internos)
        elif token['tipo'] == 'ENQUANTO':
            self.posicao += 1
            self.consumir('NAO')
            self.consumir('OBSTACULO')
            self.consumir('CHAVE_ESQ')
            comandos_internos = []
            while self.token_atual() and self.token_atual()['tipo'] != 'CHAVE_DIR':
                comandos_internos.append(self.parse_comando())
            self.consumir('CHAVE_DIR')
            return NoWhileNotObstacle(comandos_internos)
        elif token['tipo'] == 'SE':
            self.posicao += 1
            self.consumir('OBSTACULO')
            if self.token_atual() and self.token_atual()['tipo'] == 'ENTAO':
                self.posicao += 1
                comando_then = self.parse_comando()
                return NoIfObstacle(comando_then)
            else:
                self.consumir('CHAVE_ESQ')
                comandos_then = []
                while self.token_atual() and self.token_atual()['tipo'] != 'CHAVE_DIR':
                    comandos_then.append(self.parse_comando())
                self.consumir('CHAVE_DIR')
                comandos_else = []
                if self.token_atual() and self.token_atual()['tipo'] == 'SENAO':
                    self.posicao += 1
                    self.consumir('CHAVE_ESQ')
                    while self.token_atual() and self.token_atual()['tipo'] != 'CHAVE_DIR':
                        comandos_else.append(self.parse_comando())
                    self.consumir('CHAVE_DIR')
                return NoIfBlock(comandos_then, comandos_else)
        else:
            raise ErroSintaxe(f"Ação inválida ou fora de ordem: '{token['valor']}' na linha {token['linha']}.", token['linha'])

class RoverSimulador:
    def __init__(self, tamanho_celula, modo_infinito, limites_x=15, limites_y=10):
        self.tamanho_celula = tamanho_celula
        self.modo_infinito = modo_infinito
        self.limites_x = limites_x
        self.limites_y = limites_y
        self.x, self.y = 0, 0
        self.direcao = 'E'
        self.direcoes = ['N', 'E', 'S', 'W']
        self.vetores = {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}
        self.historico = []
        self.visitados = set()
        self.pilha_retorno = []
        self.seed = random.randint(0, 999999)
        self.turnos = 0
        self.diskets_coletados = set()

    def log_estado(self):
        if self.tem_disket(self.x, self.y):
            self.diskets_coletados.add((self.x, self.y))
        self.historico.append((self.x, self.y, self.direcao, self.turnos, self.diskets_coletados.copy()))

    def tem_obstaculo(self, nx, ny):
        if nx == 0 and ny == 0: return False
        if not self.modo_infinito and (nx < 0 or nx >= self.limites_x or ny < 0 or ny >= self.limites_y):
            return True
        n1 = abs(nx * 31 + ny * 17 + self.seed) % 100
        cx, cy = nx // 2, ny // 2
        n2 = abs(cx * 73 + cy * 41 + self.seed) % 100
        return n1 < 12 or n2 < 32

    def tem_disket(self, nx, ny):
        if nx == 0 and ny == 0: return False
        if self.tem_obstaculo(nx, ny): return False
        if not self.modo_infinito and (nx < 0 or nx >= self.limites_x or ny < 0 or ny >= self.limites_y):
            return False
        n = abs(nx * 123456789 + ny * 987654321 + self.seed) % 100
        return n < 8

    def mover(self, passos, direcao_movimento=1):
        vx, vy = self.vetores[self.direcao]
        for _ in range(passos):
            nx, ny = self.x + (vx * direcao_movimento), self.y + (vy * direcao_movimento)
            if not self.tem_obstaculo(nx, ny):
                self.turnos += 1
                self.x, self.y = nx, ny
                self.log_estado()
            else: break

    def girar(self, sentido):
        self.turnos += 1
        idx = self.direcoes.index(self.direcao)
        self.direcao = self.direcoes[(idx - 1) % 4] if sentido == 'ESQUERDA' else self.direcoes[(idx + 1) % 4]
        self.log_estado()

    def obstaculo_a_frente(self):
        vx, vy = self.vetores[self.direcao]
        return self.tem_obstaculo(self.x + vx, self.y + vy)

    def executar_explorar(self):
        self.turnos += 1
        self.visitados.add((self.x, self.y))
        vizinhos_validos = []
        idx_atual = self.direcoes.index(self.direcao)
        ordem = [self.direcao, self.direcoes[(idx_atual + 1) % 4], self.direcoes[(idx_atual + 3) % 4], self.direcoes[(idx_atual + 2) % 4]]
        for dir_char in ordem:
            vx, vy = self.vetores[dir_char]
            nx, ny = self.x + vx, self.y + vy
            if not self.tem_obstaculo(nx, ny) and (nx, ny) not in self.visitados:
                vizinhos_validos.append(dir_char)
        if vizinhos_validos:
            escolha = vizinhos_validos[0]
            self.pilha_retorno.append((self.x, self.y))
            self.direcao = escolha
            self.x += self.vetores[escolha][0]
            self.y += self.vetores[escolha][1]
            self.log_estado()
        elif self.pilha_retorno:
            bx, by = self.pilha_retorno.pop()
            if bx > self.x: self.direcao = 'E'
            elif bx < self.x: self.direcao = 'W'
            elif by > self.y: self.direcao = 'S'
            elif by < self.y: self.direcao = 'N'
            self.x, self.y = bx, by
            self.log_estado()

    def executar_ast(self, ast):
        self.log_estado()
        for no in ast: self.executar_no(no)

    def executar_no(self, no):
        if isinstance(no, NoComando):
            if no.acao == 'AVANCA': self.mover(no.valor, 1)
            elif no.acao == 'RECUA': self.mover(no.valor, -1)
            elif no.acao in ['ESQUERDA', 'DIREITA']:
                for _ in range(no.valor): self.girar(no.acao)
            elif no.acao == 'EXPLORAR': self.executar_explorar()
        elif isinstance(no, NoRepeat):
            if no.repeticoes == -1:
                it = 0
                while it < 5000 and self.turnos < 5000:
                    for cmd in no.comandos: self.executar_no(cmd)
                    it += 1
            else:
                for _ in range(min(no.repeticoes, 5000)):
                    for cmd in no.comandos: self.executar_no(cmd)
        elif isinstance(no, NoIfObstacle):
            if self.obstaculo_a_frente(): self.executar_no(no.comando_then)
        elif isinstance(no, NoIfBlock):
            alvo = no.comandos_then if self.obstaculo_a_frente() else no.comandos_else
            for cmd in alvo: self.executar_no(cmd)
        elif isinstance(no, NoWhileNotObstacle):
            it = 0
            while not self.obstaculo_a_frente() and it < 5000:
                for cmd in no.comandos: self.executar_no(cmd)
                it += 1

def validar_sintaxe(codigo):
    if not codigo.strip():
        return None, None
    try:
        tokens = lexer(codigo)
        Parser(tokens).parse()
        return None, None
    except ErroSintaxe as e:
        return e.linha, e.msg
    except Exception:
        return None, None

clipboard_fallback = ""
def copy_to_clipboard(texto):
    global clipboard_fallback
    clipboard_fallback = texto
    try:
        pygame.scrap.put(pygame.SCRAP_TEXT, texto.encode('utf-8'))
    except:
        pass

def get_from_clipboard():
    global clipboard_fallback
    try:
        val = pygame.scrap.get(pygame.SCRAP_TEXT)
        if val:
            return val.decode('utf-8').replace('\x00', '')
    except:
        pass
    return clipboard_fallback

def get_idx_from_pos(texto, x, y, fonte):
    linhas = texto.split('\n')
    linha_idx = min(max((y - 65) // 20, 0), len(linhas) - 1)
    if linha_idx < 0: return 0
    char_x = 110
    idx_base = sum(len(l) + 1 for l in linhas[:linha_idx])
    linha = linhas[linha_idx]
    for i, char in enumerate(linha):
        w = fonte.size(char)[0]
        if x < char_x + w / 2:
            return idx_base + i
        char_x += w
    return idx_base + len(linha)

def desenhar_simulador(simulador, arquivo_script, codigo_inicial, mensagem_erro_inicial=None):
    pygame.init()
    try:
        pygame.scrap.init()
    except:
        pass
        
    try:
        monitor_w, monitor_h = pygame.display.get_desktop_sizes()[0]
    except AttributeError:
        info_mon = pygame.display.Info()
        monitor_w, monitor_h = info_mon.current_w, info_mon.current_h

    if 'SDL_VIDEO_WINDOW_POS' in os.environ:
        del os.environ['SDL_VIDEO_WINDOW_POS']
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.font.init()
    fonte = pygame.font.SysFont("Courier", 18, bold=True)
    largura_atual, altura_atual = 900, 600
    tela = pygame.display.set_mode((largura_atual, altura_atual))
    pygame.display.set_caption("Rover Simulator")
    relogio = pygame.time.Clock()
    idx_h, t_mov = 0, time.time()
    rodando = True
    pausado = False
    modo_edicao = False
    tela_cheia = False
    modo_luz = False
    
    mensagem_erro = mensagem_erro_inicial
    
    camera_seguindo = simulador.modo_infinito
    if not camera_seguindo:
        cam_x = -(largura_atual - simulador.limites_x * 60) / 2
        cam_y = -(altura_atual - simulador.limites_y * 60) / 2
    else:
        cam_x, cam_y = 0.0, 0.0
        
    texto_codigo = codigo_inicial.replace('\r', '')
    cursor_pos = len(texto_codigo)
    sel_start = cursor_pos
    arrastando_texto = None
    mouse_pressionado = False
    
    linha_erro_rt, msg_erro_rt = validar_sintaxe(texto_codigo)
    historico_edicao = []
    
    paleta_comandos = ['AVANCA = 1', 'RECUA = 1', 'ESQUERDA', 'ESQUERDA = 1', 'DIREITA', 'EXPLORAR', 'REPITA {', 'REPITA = 4 {', '}', 'ENQUANTO NAO OBSTACULO {', 'SE OBSTACULO ENTAO']
    paleta_ui = []
    y_offset = 60
    for cmd in paleta_comandos:
        palavras = cmd.split(' ')
        linhas_cmd = []
        linha_atual = palavras[0]
        for p in palavras[1:]:
            if fonte.size(linha_atual + " " + p)[0] < 180:
                linha_atual += " " + p
            else:
                linhas_cmd.append(linha_atual)
                linha_atual = p
        linhas_cmd.append(linha_atual)
        altura_caixa = len(linhas_cmd) * 20 + 10
        rect = pygame.Rect(630, y_offset, 200, altura_caixa)
        paleta_ui.append({'cmd': cmd, 'linhas': linhas_cmd, 'rect': rect})
        y_offset += altura_caixa + 10
        
    btn_pause = pygame.Rect(10, 10, 80, 35)
    btn_editor = pygame.Rect(100, 10, 85, 35)
    btn_salvar = pygame.Rect(195, 10, 85, 35)
    btn_fullscreen = pygame.Rect(290, 10, 125, 35)
    btn_regerar = pygame.Rect(425, 10, 100, 35)
    btn_luz = pygame.Rect(535, 10, 95, 35)
    caixa_texto_rect = pygame.Rect(60, 60, 550, 480)

    while rodando:
        mouse_pos = pygame.mouse.get_pos()
        codigo_anterior = texto_codigo
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    rodando = False
                mensagem_erro = None
                if modo_edicao:
                    mods = pygame.key.get_mods()
                    ctrl = mods & pygame.KMOD_CTRL
                    if ctrl:
                        if ev.key == pygame.K_a:
                            sel_start = 0
                            cursor_pos = len(texto_codigo)
                        elif ev.key == pygame.K_c:
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            if s != e: copy_to_clipboard(texto_codigo[s:e])
                        elif ev.key == pygame.K_x:
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            if s != e:
                                historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                                if len(historico_edicao) > 200: historico_edicao.pop(0)
                                copy_to_clipboard(texto_codigo[s:e])
                                texto_codigo = texto_codigo[:s] + texto_codigo[e:]
                                cursor_pos = sel_start = s
                        elif ev.key == pygame.K_v:
                            txt = get_from_clipboard()
                            if txt:
                                historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                                if len(historico_edicao) > 200: historico_edicao.pop(0)
                                txt = txt.upper()
                                s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                                texto_codigo = texto_codigo[:s] + txt + texto_codigo[e:]
                                cursor_pos = sel_start = s + len(txt)
                        elif ev.key == pygame.K_z:
                            if historico_edicao:
                                texto_codigo, cursor_pos, sel_start = historico_edicao.pop()
                    else:
                        if ev.key == pygame.K_BACKSPACE:
                            historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                            if len(historico_edicao) > 200: historico_edicao.pop(0)
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            if s != e:
                                texto_codigo = texto_codigo[:s] + texto_codigo[e:]
                                cursor_pos = sel_start = s
                            elif cursor_pos > 0:
                                texto_codigo = texto_codigo[:cursor_pos-1] + texto_codigo[cursor_pos:]
                                cursor_pos -= 1
                                sel_start = cursor_pos
                        elif ev.key == pygame.K_DELETE:
                            historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                            if len(historico_edicao) > 200: historico_edicao.pop(0)
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            if s != e:
                                texto_codigo = texto_codigo[:s] + texto_codigo[e:]
                                cursor_pos = sel_start = s
                            elif cursor_pos < len(texto_codigo):
                                texto_codigo = texto_codigo[:cursor_pos] + texto_codigo[cursor_pos+1:]
                        elif ev.key == pygame.K_RETURN:
                            historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                            if len(historico_edicao) > 200: historico_edicao.pop(0)
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            texto_codigo = texto_codigo[:s] + '\n' + texto_codigo[e:]
                            cursor_pos = sel_start = s + 1
                        elif ev.key == pygame.K_LEFT:
                            cursor_pos = max(0, cursor_pos - 1)
                            if not (mods & pygame.KMOD_SHIFT): sel_start = cursor_pos
                        elif ev.key == pygame.K_RIGHT:
                            cursor_pos = min(len(texto_codigo), cursor_pos + 1)
                            if not (mods & pygame.KMOD_SHIFT): sel_start = cursor_pos
                        elif ev.key == pygame.K_UP or ev.key == pygame.K_DOWN:
                            pass
                        elif ev.key == pygame.K_TAB:
                            historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                            if len(historico_edicao) > 200: historico_edicao.pop(0)
                            s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                            texto_codigo = texto_codigo[:s] + '\t' + texto_codigo[e:]
                            cursor_pos = sel_start = s + 1
                        else:
                            char = ev.unicode.upper()
                            if char.isprintable() and char != '':
                                historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                                if len(historico_edicao) > 200: historico_edicao.pop(0)
                                s, e = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
                                texto_codigo = texto_codigo[:s] + char + texto_codigo[e:]
                                cursor_pos = sel_start = s + len(char)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if modo_edicao and caixa_texto_rect.collidepoint(ev.pos):
                    mensagem_erro = None
                    idx = get_idx_from_pos(texto_codigo, ev.pos[0], ev.pos[1], fonte)
                    cursor_pos = sel_start = idx
                    mouse_pressionado = True
                if btn_pause.collidepoint(ev.pos): pausado = not pausado
                elif btn_editor.collidepoint(ev.pos): modo_edicao = not modo_edicao
                elif btn_luz.collidepoint(ev.pos): modo_luz = not modo_luz
                elif btn_fullscreen.collidepoint(ev.pos):
                    tela_cheia = not tela_cheia
                    if tela_cheia:
                        if 'SDL_VIDEO_CENTERED' in os.environ:
                            del os.environ['SDL_VIDEO_CENTERED']
                        os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
                        tela = pygame.display.set_mode((monitor_w, monitor_h), pygame.NOFRAME)
                        try:
                            hwnd = pygame.display.get_wm_info()["window"]
                            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, monitor_w, monitor_h, 0x0040)
                        except: pass
                    else:
                        if 'SDL_VIDEO_WINDOW_POS' in os.environ:
                            del os.environ['SDL_VIDEO_WINDOW_POS']
                        os.environ['SDL_VIDEO_CENTERED'] = '1'
                        tela = pygame.display.set_mode((900, 600))
                        try:
                            hwnd = pygame.display.get_wm_info()["window"]
                            x = (monitor_w - 900) // 2
                            y = (monitor_h - 600) // 2
                            ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 900, 600, 0x0040)
                        except: pass
                    
                    largura_atual, altura_atual = tela.get_size()
                    if not camera_seguindo and not simulador.modo_infinito:
                        cam_x = -(largura_atual - simulador.limites_x * 60) / 2
                        cam_y = -(altura_atual - simulador.limites_y * 60) / 2
                elif btn_salvar.collidepoint(ev.pos):
                    if msg_erro_rt:
                        mensagem_erro = msg_erro_rt
                    else:
                        try:
                            with open(arquivo_script, 'w', encoding='utf-8') as f: f.write(texto_codigo)
                            tokens = lexer(texto_codigo)
                            modo, ast = Parser(tokens).parse()
                            lim_x = largura_atual // 60
                            lim_y = altura_atual // 60
                            novo_sim = RoverSimulador(60, modo, lim_x, lim_y)
                            novo_sim.seed = simulador.seed
                            novo_sim.executar_ast(ast)
                            simulador = novo_sim
                            idx_h = 0
                            mensagem_erro = None
                            if not modo:
                                cam_x = -(largura_atual - lim_x * 60) / 2
                                cam_y = -(altura_atual - lim_y * 60) / 2
                                camera_seguindo = False
                        except Exception as e:
                            mensagem_erro = f"ERRO: {e}"
                elif btn_regerar.collidepoint(ev.pos):
                    if msg_erro_rt:
                        mensagem_erro = msg_erro_rt
                    else:
                        try:
                            tokens = lexer(texto_codigo)
                            modo, ast = Parser(tokens).parse()
                            lim_x = largura_atual // 60
                            lim_y = altura_atual // 60
                            novo_sim = RoverSimulador(60, modo, lim_x, lim_y)
                            novo_sim.executar_ast(ast)
                            simulador = novo_sim
                            idx_h = 0
                            mensagem_erro = None
                            if not modo:
                                cam_x = -(largura_atual - lim_x * 60) / 2
                                cam_y = -(altura_atual - lim_y * 60) / 2
                                camera_seguindo = False
                        except Exception as e:
                            mensagem_erro = f"ERRO AO REGERAR: {e}"
                if modo_edicao:
                    for item in paleta_ui:
                        if item['rect'].collidepoint(ev.pos):
                            arrastando_texto = item['cmd']
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                mouse_pressionado = False
                if arrastando_texto:
                    if caixa_texto_rect.collidepoint(ev.pos):
                        historico_edicao.append((texto_codigo, cursor_pos, sel_start))
                        if len(historico_edicao) > 200: historico_edicao.pop(0)
                        idx = get_idx_from_pos(texto_codigo, ev.pos[0], ev.pos[1], fonte)
                        texto_codigo = texto_codigo[:idx] + arrastando_texto + texto_codigo[idx:]
                        cursor_pos = sel_start = idx + len(arrastando_texto)
                    arrastando_texto = None
            elif ev.type == pygame.MOUSEMOTION:
                if mouse_pressionado and caixa_texto_rect.collidepoint(ev.pos):
                    cursor_pos = get_idx_from_pos(texto_codigo, ev.pos[0], ev.pos[1], fonte)

        if texto_codigo != codigo_anterior:
            linha_erro_rt, msg_erro_rt = validar_sintaxe(texto_codigo)

        teclas = pygame.key.get_pressed()
        if not modo_edicao:
            vel_cam = 15
            if teclas[pygame.K_LEFT]: cam_x -= vel_cam; camera_seguindo = False
            if teclas[pygame.K_RIGHT]: cam_x += vel_cam; camera_seguindo = False
            if teclas[pygame.K_UP]: cam_y -= vel_cam; camera_seguindo = False
            if teclas[pygame.K_DOWN]: cam_y += vel_cam; camera_seguindo = False
            if teclas[pygame.K_SPACE]: camera_seguindo = True

        agora = time.time()
        if not pausado and agora - t_mov > 0.06 and idx_h < len(simulador.historico) - 1:
            idx_h += 1
            t_mov = agora
            
        tela.fill((30, 30, 30))
        
        if simulador.historico:
            rx, ry, rdir, turnos_atuais, diskets_atuais = simulador.historico[idx_h]
        else:
            rx, ry, rdir, turnos_atuais, diskets_atuais = 0, 0, 'E', 0, set()
            
        px_r, py_r = rx * 60 + 30, ry * 60 + 30
        
        if camera_seguindo:
            cam_x += ((px_r - largura_atual//2) - cam_x) * 0.1
            cam_y += ((py_r - altura_atual//2) - cam_y) * 0.1

        start_x = int(cam_x) // 60 - 1
        start_y = int(cam_y) // 60 - 1
        alcance_x = int(largura_atual // 60) + 3
        alcance_y = int(altura_atual // 60) + 3
        
        for x in range(start_x, start_x + alcance_x):
            for y in range(start_y, start_y + alcance_y):
                rect = pygame.Rect(x*60 - int(cam_x), y*60 - int(cam_y), 60, 60)
                pygame.draw.rect(tela, (30, 30, 35), rect)
                pygame.draw.rect(tela, (50, 50, 60), rect, 1)
                
                if simulador.tem_obstaculo(x, y):
                    if not simulador.modo_infinito and (x < 0 or x >= simulador.limites_x or y < 0 or y >= simulador.limites_y):
                        pygame.draw.rect(tela, (40, 20, 20), rect)
                        pygame.draw.rect(tela, (20, 10, 10), rect, 1)
                    else:
                        cor_fundo = (200, 50, 50) if modo_luz else (60, 30, 30)
                        cor_borda = (100, 20, 20) if modo_luz else (40, 20, 20)
                        pygame.draw.rect(tela, cor_fundo, rect)
                        pygame.draw.rect(tela, cor_borda, rect, 1)
                elif simulador.tem_disket(x, y) and (x, y) not in diskets_atuais:
                    pygame.draw.rect(tela, (50, 150, 255), (rect.x + 15, rect.y + 15, 30, 30), border_radius=4)
                    pygame.draw.rect(tela, (200, 255, 255), (rect.x + 18, rect.y + 18, 10, 10))

        px_tela, py_tela = px_r - int(cam_x), py_r - int(cam_y)
        pygame.draw.circle(tela, (50, 200, 50), (px_tela, py_tela), 20)
        p_x, p_y = px_tela, py_tela
        if rdir == 'N': p_y -= 20
        elif rdir == 'S': p_y += 20
        elif rdir == 'E': p_x += 20
        elif rdir == 'W': p_x -= 20
        pygame.draw.line(tela, (255, 255, 255), (px_tela, py_tela), (p_x, p_y), 4)

        botoes = [
            (btn_pause, "Cont." if pausado else "Pausar"),
            (btn_editor, "Editor"),
            (btn_salvar, "Rodar"),
            (btn_fullscreen, "Tela Cheia"),
            (btn_regerar, "Regerar"),
            (btn_luz, "Luz: ON" if modo_luz else "Luz: OFF")
        ]
        
        for b, t in botoes:
            cor_btn = (130, 130, 140) if b.collidepoint(mouse_pos) else (100, 100, 110)
            pygame.draw.rect(tela, cor_btn, b, border_radius=6)
            pygame.draw.rect(tela, (60, 60, 70), b, 2, border_radius=6)
            texto_render = fonte.render(t, True, (255, 255, 255))
            txt_x = b.x + (b.width - texto_render.get_width()) // 2
            txt_y = b.y + (b.height - texto_render.get_height()) // 2
            tela.blit(texto_render, (txt_x, txt_y))

        painel_placar = pygame.Surface((220, 100))
        painel_placar.set_alpha(220)
        painel_placar.fill((20, 20, 25))
        tela.blit(painel_placar, (largura_atual - 230, 10))
        tela.blit(fonte.render(f"Turnos: {turnos_atuais}", True, (200, 200, 200)), (largura_atual - 220, 20))
        tela.blit(fonte.render(f"Diskets: {len(diskets_atuais)}", True, (50, 150, 255)), (largura_atual - 220, 50))
        pontos_totais = (len(diskets_atuais) * 100) - turnos_atuais
        tela.blit(fonte.render(f"Pontos: {pontos_totais}", True, (255, 215, 0)), (largura_atual - 220, 80))

        if modo_edicao:
            pygame.draw.rect(tela, (20, 20, 20), (50, 50, 800, 500), border_radius=10)
            pygame.draw.rect(tela, (40, 40, 40), caixa_texto_rect, border_radius=5)
            linhas = texto_codigo.split('\n')
            acc_chars = 0
            s_s, e_s = min(cursor_pos, sel_start), max(cursor_pos, sel_start)
            
            for i, linha in enumerate(linhas):
                y_pos = 65 + i * 20
                if 65 <= y_pos <= 520:
                    tela.blit(fonte.render(str(i + 1), True, (150, 150, 150)), (65, y_pos))
                    
                    c_x = 110
                    for j, char in enumerate(linha):
                        idx = acc_chars + j
                        w = fonte.size(char)[0]
                        if s_s <= idx < e_s:
                            pygame.draw.rect(tela, (0, 100, 200), (c_x, y_pos, w, 20))
                        c_x += w
                    if s_s <= acc_chars + len(linha) < e_s:
                        pygame.draw.rect(tela, (0, 100, 200), (c_x, y_pos, 8, 20))
                        
                    tela.blit(fonte.render(linha, True, (255, 255, 255)), (110, y_pos))
                    
                    if linha_erro_rt and (i + 1) == linha_erro_rt:
                        w_linha = max(fonte.size(linha)[0], 10)
                        pygame.draw.line(tela, (255, 50, 50), (110, y_pos + 18), (110 + w_linha, y_pos + 18), 3)
                        
                    if acc_chars <= cursor_pos <= acc_chars + len(linha):
                        c_idx = cursor_pos - acc_chars
                        c_x = 110 + fonte.size(linha[:c_idx])[0]
                        if int(time.time() * 2) % 2 == 0:
                            pygame.draw.line(tela, (255, 255, 255), (c_x, y_pos), (c_x, y_pos + 18), 2)
                acc_chars += len(linha) + 1
                
            for item in paleta_ui:
                rect = item['rect']
                cor_paleta = (100, 100, 170) if rect.collidepoint(mouse_pos) else (80, 80, 150)
                pygame.draw.rect(tela, cor_paleta, rect, border_radius=5)
                for j, linha_texto in enumerate(item['linhas']):
                    tela.blit(fonte.render(linha_texto, True, (255, 255, 255)), (rect.x + 10, rect.y + 6 + j * 20))
            
            if msg_erro_rt:
                tela.blit(fonte.render(msg_erro_rt, True, (255, 100, 100)), (65, 545))
            else:
                tela.blit(fonte.render("Sintaxe correta", True, (100, 255, 100)), (65, 545))
                    
        if mensagem_erro:
            rect_erro = pygame.Rect(largura_atual // 2 - 350, altura_atual // 2 - 50, 700, 100)
            pygame.draw.rect(tela, (180, 40, 40), rect_erro, border_radius=8)
            pygame.draw.rect(tela, (255, 100, 100), rect_erro, 3, border_radius=8)
            texto_erro = fonte.render(mensagem_erro, True, (255, 255, 255))
            tela.blit(texto_erro, (rect_erro.centerx - texto_erro.get_width()//2, rect_erro.centery - 20))
            fonte_pequena = pygame.font.SysFont("Courier", 14, bold=False)
            texto_dica = fonte_pequena.render("(Clique no editor ou digite para fechar e corrigir)", True, (255, 200, 200))
            tela.blit(texto_dica, (rect_erro.centerx - texto_dica.get_width()//2, rect_erro.centery + 15))

        if arrastando_texto: tela.blit(fonte.render(arrastando_texto, True, (200, 200, 50)), mouse_pos)
        pygame.display.flip()
        relogio.tick(60)
    pygame.quit()

def executar(arquivo_script):
    try:
        with open(arquivo_script, 'r', encoding='utf-8') as f: raw = f.read().strip()
        
        if os.path.exists(raw) and (raw.endswith('.txt') or raw.endswith('.genshin')):
            with open(raw, 'r', encoding='utf-8') as f2: codigo = f2.read()
            arq_real = raw
        else:
            codigo, arq_real = raw, arquivo_script
            
        mensagem_erro = None
        sim = None
        
        try:
            tokens = lexer(codigo)
            modo, ast = Parser(tokens).parse()
            sim = RoverSimulador(60, modo, 15, 10)
            sim.executar_ast(ast)
        except ErroSintaxe as e:
            mensagem_erro = e.msg
            sim = RoverSimulador(60, False, 15, 10)
        except Exception as e:
            mensagem_erro = f"ERRO INICIAL: {e}"
            sim = RoverSimulador(60, False, 15, 10)
            
        desenhar_simulador(sim, arq_real, codigo, mensagem_erro)
    except Exception as e:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sim_vazio = RoverSimulador(60, False, 15, 10)
        desenhar_simulador(sim_vazio, "script_vazio.txt", "", None)
    else:
        executar(sys.argv[1])