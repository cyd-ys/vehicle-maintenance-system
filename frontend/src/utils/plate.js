/**
 * 车牌号规则、常用品牌车型数据与校验工具
 *
 * 国内车牌规则：
 *  - 普通车牌 7 位：省份简称 + 发牌机关字母 + 5 位序号（数字/字母）
 *  - 新能源车牌 8 位：
 *      · 小型车 第 3 位为 D（纯电）或 F（非纯电），后接 5 位序号
 *      · 大型车 第 8 位为 D 或 F
 *  - 全车牌不使用字母 I 和 O（易与 1、0 混淆）
 *  - 普通车牌序号末位可为 挂 / 学 / 警 / 港 / 澳
 */

/** 省份简称（含直辖市、自治区） */
export const PROVINCES = [
  { code: '京', name: '北京' }, { code: '津', name: '天津' }, { code: '冀', name: '河北' },
  { code: '晋', name: '山西' }, { code: '蒙', name: '内蒙古' }, { code: '辽', name: '辽宁' },
  { code: '吉', name: '吉林' }, { code: '黑', name: '黑龙江' }, { code: '沪', name: '上海' },
  { code: '苏', name: '江苏' }, { code: '浙', name: '浙江' }, { code: '皖', name: '安徽' },
  { code: '闽', name: '福建' }, { code: '赣', name: '江西' }, { code: '鲁', name: '山东' },
  { code: '豫', name: '河南' }, { code: '鄂', name: '湖北' }, { code: '湘', name: '湖南' },
  { code: '粤', name: '广东' }, { code: '桂', name: '广西' }, { code: '琼', name: '海南' },
  { code: '渝', name: '重庆' }, { code: '川', name: '四川' }, { code: '贵', name: '贵州' },
  { code: '云', name: '云南' }, { code: '藏', name: '西藏' }, { code: '陕', name: '陕西' },
  { code: '甘', name: '甘肃' }, { code: '青', name: '青海' }, { code: '宁', name: '宁夏' },
  { code: '新', name: '新疆' }
]

/** 常用汽车品牌与车型（可搜索，也允许自行输入） */
export const BRANDS = [
  { name: '大众', models: ['朗逸', '速腾', '迈腾', '帕萨特', '宝来', '高尔夫', '途观L', '探岳', 'ID.3', 'ID.4 X'] },
  { name: '丰田', models: ['卡罗拉', '雷凌', '凯美瑞', '亚洲龙', '汉兰达', 'RAV4荣放', '威兰达', '锋兰达'] },
  { name: '本田', models: ['雅阁', '思域', '型格', '飞度', 'CR-V', '皓影', '冠道', 'XR-V'] },
  { name: '日产', models: ['轩逸', '天籁', '逍客', '奇骏', '骐达', '劲客'] },
  { name: '别克', models: ['英朗', '威朗', '君威', '君越', '昂科威', '昂科拉'] },
  { name: '奔驰', models: ['A级', 'C级', 'E级', 'S级', 'GLA', 'GLB', 'GLC', 'GLE', 'EQE'] },
  { name: '宝马', models: ['1系', '3系', '5系', '7系', 'X1', 'X3', 'X5', 'i3', 'iX3'] },
  { name: '奥迪', models: ['A3', 'A4L', 'A6L', 'Q2L', 'Q3', 'Q5L', 'Q7', 'e-tron'] },
  { name: '比亚迪', models: ['秦PLUS', '汉', '宋PLUS', '唐', '元PLUS', '海豚', '海豹', '驱逐舰05'] },
  { name: '吉利', models: ['帝豪', '星瑞', '星越L', '博越', '缤越', '银河L7'] },
  { name: '长安', models: ['逸动', 'CS75 PLUS', 'CS55 PLUS', 'UNI-V', 'UNI-K', '深蓝SL03'] },
  { name: '奇瑞', models: ['艾瑞泽8', '瑞虎8', '瑞虎7', '风云A8', '星途凌云'] },
  { name: '五菱', models: ['宏光MINIEV', '五菱宏光', '星光', '缤果', '佳辰'] },
  { name: '哈弗', models: ['H6', 'H9', '大狗', '猛龙', '枭龙MAX'] },
  { name: '荣威', models: ['RX5', 'i5', 'D5X', 'iMAX8'] },
  { name: '名爵', models: ['MG5', 'MG6', 'MG7', 'ZS', 'HS'] },
  { name: '红旗', models: ['H5', 'H9', 'HS5', 'HS7', 'E-QM5', 'EH7'] },
  { name: '领克', models: ['01', '02', '03', '05', '08', '09'] },
  { name: '魏牌', models: ['摩卡', '拿铁', '蓝山', '高山'] },
  { name: '特斯拉', models: ['Model 3', 'Model Y', 'Model S', 'Model X'] },
  { name: '蔚来', models: ['ES6', 'ES8', 'ET5', 'ET7', 'EC6'] },
  { name: '小鹏', models: ['P5', 'P7', 'G6', 'G9', 'X9'] },
  { name: '理想', models: ['L6', 'L7', 'L8', 'L9', 'MEGA'] },
  { name: '埃安', models: ['AION S', 'AION Y', 'AION V', 'AION LX'] },
  { name: '零跑', models: ['T03', 'C10', 'C11', 'C16'] },
  { name: '极氪', models: ['001', '007', 'X', '009'] },
  { name: '哪吒', models: ['哪吒U', '哪吒V', '哪吒S', '哪吒L'] },
  { name: '现代', models: ['伊兰特', '途胜L', '索纳塔', 'ix35'] },
  { name: '起亚', models: ['K3', 'K5', '智跑', '狮铂拓界'] },
  { name: '马自达', models: ['昂克赛拉', '阿特兹', 'CX-5', 'CX-50'] },
  { name: '沃尔沃', models: ['S60', 'S90', 'XC40', 'XC60', 'XC90'] },
  { name: '福特', models: ['福克斯', '蒙迪欧', '锐界L', '探险者'] },
  { name: '雪佛兰', models: ['科鲁泽', '迈锐宝XL', '探界者'] },
  { name: '斯柯达', models: ['明锐', '速派', '柯迪亚克'] },
  { name: '标致', models: ['408', '508L', '4008'] },
  { name: '雪铁龙', models: ['凡尔赛C5X', '天逸', 'C3-XR'] },
  { name: '保时捷', models: ['Macan', 'Cayenne', 'Panamera', 'Taycan'] }
]

export function getModels(brand) {
  const hit = BRANDS.find((b) => b.name === brand)
  return hit ? hit.models : []
}

// 省份简称串
const PROVINCE_CHARS = PROVINCES.map((p) => p.code).join('')
// 字母：排除 I、O
const LETTER = 'A-HJ-NP-Z'
// 数字或字母（不含 I、O）
const CHAR = 'A-HJ-NP-Z0-9'

const RE_PLATE = new RegExp(
  '^[' + PROVINCE_CHARS + '][' + LETTER + '](?:' +
  '[' + CHAR + ']{4}[0-9A-HJ-NP-Z挂学警港澳]' + '|' + // 普通 7 位
  '[DF][' + CHAR + ']{5}' + '|' +                     // 小型新能源 8 位
  '[' + CHAR + ']{5}[DF]' +                           // 大型新能源 8 位
  ')$'
)

/** 清洗"字母+数字"部分：转大写、去非法字符、禁用 I/O */
export function sanitizePlateRest(input) {
  return (input || '')
    .toUpperCase()
    .replace(/[^0-9A-Z挂学警港澳]/g, '')
    .replace(/[IO]/g, '')
    .slice(0, 7)
}

/**
 * 校验完整车牌号
 * @returns {{ ok: boolean, message: string, kind?: 'normal'|'nev' }}
 */
export function validatePlate(value) {
  const v = (value || '').trim().toUpperCase()
  if (!v) return { ok: false, message: '请输入车牌号' }
  if (/[IO]/.test(v)) return { ok: false, message: '车牌号不包含字母 I 和 O，请确认' }
  if (v.length !== 7 && v.length !== 8) {
    return { ok: false, message: '普通车牌为 7 位，新能源车牌为 8 位' }
  }
  if (!PROVINCE_CHARS.includes(v[0])) {
    return { ok: false, message: '第 1 位应为省份简称，如 京 / 湘 / 琼' }
  }
  if (!new RegExp('^[' + LETTER + ']$').test(v[1])) {
    return { ok: false, message: '第 2 位应为发牌机关字母（不含 I、O）' }
  }
  if (!RE_PLATE.test(v)) {
    if (v.length === 8) {
      return { ok: false, message: '新能源车牌需第 3 位或第 8 位为 D / F' }
    }
    return { ok: false, message: '车牌号格式不正确，请检查后重新输入' }
  }
  if (v.length === 8) {
    const small = v[2] === 'D' || v[2] === 'F'
    return { ok: true, message: `新能源车牌（${small ? '小型车' : '大型车'}）`, kind: 'nev' }
  }
  return { ok: true, message: '普通车牌', kind: 'normal' }
}
